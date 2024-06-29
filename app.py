from flask import Flask, request, jsonify, render_template, send_file
import requests
import pyttsx3
import random
from openpyxl import Workbook
from io import BytesIO

app = Flask(__name__)

# Mapping the original class types to the new names
class_type_mapping = {
    "ci_with": "Contraindications",
    "ci_moa": "Contraindications (MoA)",
    "ci_pe": "Contraindications (Effects)",
    "ci_chemclass": "Contraindications (Chem)",
    "has_pe": "Effects",
    "has_moa": "MoA",
    "has_epc": "Drug Class",
    "may_treat": "To Treat"
}

ordered_class_types = [
    "ci_with", "ci_moa", "ci_pe", "ci_chemclass", "has_pe", "has_moa", "has_epc", "may_treat"
]

jokes = [
    "Aristotle: To actualize its potential.",
    "Plato: For the greater good.",
    "Socrates: To examine the other side.",
    "Descartes: It had sufficient reason to believe it was dreaming.",
    "Hume: Out of habit.",
    "Kant: Out of a sense of duty.",
    "Nietzsche: Because if you gaze too long across the road, the road gazes also across you.",
    "Hegel: To fulfill the dialectical progression.",
    "Marx: It was a historical inevitability.",
    "Sartre: In order to act in good faith and be true to itself.",
    "Camus: One must imagine Sisyphus happy and the chicken crossing the road.",
    "Wittgenstein: The meaning of 'cross' was in the use, not in the action.",
    "Derrida: The chicken was making a deconstructive statement on the binary opposition of 'this side' and 'that side.'",
    "Heidegger: To authentically dwell in the world.",
    "Foucault: Because of the societal structures and power dynamics at play.",
    "Chomsky: For a syntactic, not pragmatic, purpose.",
    "Buddha: If you meet the chicken on the road, kill it.",
    "Laozi: The chicken follows its path naturally.",
    "Confucius: The chicken crossed the road to reach the state of Ren.",
    "Leibniz: In the best of all possible worlds, the chicken would cross the road."
]

class_cache = {}  # Cache for storing drug class data

@app.route('/')
def index():
    selected_joke = random.choice(jokes)
    return render_template('index.html', quote=selected_joke)

@app.route('/get_drug_class', methods=['POST'])
def get_drug_class():
    drug_name = request.json.get('drug_name')
    if not drug_name:
        return jsonify({'error': 'No drug name provided'}), 400

    # Check if the drug class data is cached
    if drug_name in class_cache:
        return jsonify(class_cache[drug_name])

    class_types = {rela: set() for rela in ordered_class_types}

    for rela in ordered_class_types:
        # Use the RxClass API to get drug class information
        url = f"https://rxnav.nlm.nih.gov/REST/rxclass/class/byDrugName.json?drugName={drug_name}&relaSource=ALL&relas={rela}"
        response = requests.get(url)
        if response.status_code != 200:
            return jsonify({'error': 'Failed to fetch data from RxClass API'}), 500

        data = response.json()
        if 'rxclassDrugInfoList' in data:
            drug_classes = data['rxclassDrugInfoList']['rxclassDrugInfo']
            for cls in drug_classes:
                class_name = cls['rxclassMinConceptItem']['className']
                class_types[rela].add(class_name)

    # Mapping and ordering the results
    mapped_classes = {class_type_mapping[rela]: list(class_types[rela]) for rela in ordered_class_types}

    # Cache the drug class data
    class_cache[drug_name] = {'drug_name': drug_name, 'classes': mapped_classes}

    return jsonify({'drug_name': drug_name, 'classes': mapped_classes})

@app.route('/speak', methods=['POST'])
def speak():
    text = request.json.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400

    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()

    return jsonify({'status': 'success'})

@app.route('/download_results', methods=['POST'])
def download_results():
    drug_name = request.json.get('drug_name')
    if not drug_name:
        return jsonify({'error': 'No drug name provided'}), 400

    # Check if the drug class data is cached
    if drug_name not in class_cache:
        return jsonify({'error': 'Drug class data not found'}), 404

    drug_class_data = class_cache[drug_name]

    # Create Excel workbook
    wb = Workbook()
    ws = wb.active
    ws.append(['Class Type', 'Classes'])
    for class_type, classes in drug_class_data['classes'].items():
        ws.append([class_type, ', '.join(classes)])

    # Save workbook to BytesIO buffer
    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    return send_file(buffer, attachment_filename=f'{drug_name}_drug_class_results.xlsx', as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)