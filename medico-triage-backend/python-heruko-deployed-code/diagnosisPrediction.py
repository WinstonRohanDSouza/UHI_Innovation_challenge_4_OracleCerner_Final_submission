import os
import json
import pandas as pd
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS, cross_origin

app = Flask(__name__)
cors = CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

@app.route("/recommendationBasisDiagnosis",methods=['POST'])
def departmentPrediction():
    # Get the diagnosis for which department needs to be recommended
    input_diagnosis = request.json['diagnosis']
    diagnosis_string = [x.lower() for x in input_diagnosis][0]
    # import/load the json which has data for department, treatments and investigation
    file_path = open('department.json')
    diagnois_department_data = json.load(file_path)

    if diagnois_department_data.get(str(diagnosis_string).strip()) == None :
        return json.dumps({"Status":"Success", "recommendation": "no recommendation"}) 
    else :
        return json.dumps({"Status":"Success","recommendation":diagnois_department_data[diagnosis_string]})


@app.route("/diagnoisPrediction",methods=['POST'])
def diagnoisPrediction():
    f_path = "Symptom-Diagnosis-Linear-matrix.xlsx"
    sheet_name = "Sheet1"
    input_symptoms = request.json['symptoms']
    input_symptoms = [x.lower() for x in input_symptoms]
    # reading excel and checking column names for creating diagnosis dataframe
    diagnosis_column = [0]
    df_diagnosis = pd.read_excel(
        f_path, sheet_name=sheet_name, engine='openpyxl', usecols=diagnosis_column)

    # reading excel and checking column names for creating symptom dataframe
    df_read_all_data_subset = pd.read_excel(f_path, sheet_name=sheet_name, engine='openpyxl')
    list_symptoms = df_read_all_data_subset.head(0)

    df_diagnosis_symptom_zero_one_matrix = df_read_all_data_subset.copy() 
    # droping diagnosis column from the datafram
    df_diagnosis_symptom_zero_one_matrix = df_diagnosis_symptom_zero_one_matrix.iloc[: , 1:]

    # creating a symptom list using the dataframe header
    input_symptom_zero_one_matrix = []
    list_symptoms = [x.lower() for x in list_symptoms]
    for symptom in list_symptoms :
        if symptom in input_symptoms :
            input_symptom_zero_one_matrix.append(1)
        else :
            input_symptom_zero_one_matrix.append(0)     
    # removing empty first column from the symptoms row
    input_symptom_zero_one_matrix.pop(0)

    # calculating cosine similarity
    symptom_zero_one_list = df_diagnosis_symptom_zero_one_matrix.to_numpy()
    input_symptom_zero_one_list = np.array(input_symptom_zero_one_matrix)
    similarity_scores = symptom_zero_one_list.dot(input_symptom_zero_one_list)/ (np.linalg.norm(symptom_zero_one_list, axis=1) * np.linalg.norm(input_symptom_zero_one_list))

    # creating a new DataFrame with diagnosis and cosine similarity value
    df_diagnosis_list_similarity_scores = pd.DataFrame()
    df_diagnosis_list_similarity_scores['Diagnosis'] = df_diagnosis.copy()
    df_diagnosis_list_similarity_scores['Similarity-Score'] = similarity_scores
    df_sorted_diagnosis = df_diagnosis_list_similarity_scores.sort_values(by=['Similarity-Score'], ascending=False).head(7)

    # deleting diagnois if cosine similarity not greater than 0
    df_sorted_diagnosis = df_sorted_diagnosis[df_sorted_diagnosis['Similarity-Score'] > 0]
    return json.dumps({"Status":"Success","predicted_diagnosis":df_sorted_diagnosis.to_json(orient='records')})

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

