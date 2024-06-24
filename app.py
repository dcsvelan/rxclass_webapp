from flask import Flask, request, jsonify, render_template
import requests
import pyttsx3

app = Flask(__name__)

# Mapping the original class types to the new names
class_type_mapping = {
    "ci_with": "Contraindications",
    "ci_moa": "Contraindications (MoA)",
    "ci_pe": "Contraindications (Effects)",
    "ci_chemclass": "Contraindications (Chem)",
    "may_treat": "To Treat",
    "has_moa": "MoA",
    "has_pe": "Effects"
}

ordered_class_types = [
    "ci_with", "ci_moa", "ci_pe", "ci_chemclass", "may_treat", "has_moa", "has_pe"
]

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_drug_class', methods=['POST'])
def get_drug_class():
    drug_name = request.json.get('drug_name')
    if not drug_name:
        return jsonify({'error': 'No drug name provided'}), 400

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

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)