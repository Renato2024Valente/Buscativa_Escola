from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from bson.objectid import ObjectId
from datetime import datetime
import os

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

client = MongoClient("mongodb+srv://bicudo:bicudo25@cluster0.fik4cee.mongodb.net/?retryWrites=true&w=majority&tls=true")
db = client["buscativa_escolar"]
colecao_frequencia = db["frequencia"]
colecao_buscativa = db["registro"]

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/frequencia")
def frequencia():
    return render_template("frequencia.html")

@app.route("/buscativa")
def buscativa_page():
    return render_template("buscativa.html")

@app.route("/api/frequencia", methods=["POST"])
def registrar_frequencia():
    dados = request.json
    aluno = dados["aluno"]
    serie = dados["serie"]
    presencas = int(dados["presencas"])
    aulas = int(dados["aulas"])
    freq = round((presencas / aulas) * 100, 2)

    doc = {
        "aluno": aluno,
        "serie": serie,
        "presencas": presencas,
        "aulas": aulas,
        "frequencia": freq,
        "dataRegistro": datetime.now()
    }

    colecao_frequencia.insert_one(doc)

    if freq < 80:
        alerta = {
            "aluno": aluno,
            "serie": serie,
            "dataFalta": datetime.now().strftime("%Y-%m-%d"),
            "tipoContato": "Sistema Frequência",
            "responsavel": "Sistema Frequência",
            "resultado": f"Frequência abaixo de {freq}%",
            "observacoes": "",
            "dataRegistro": datetime.now()
        }
        colecao_buscativa.insert_one(alerta)

    return jsonify({"status": "success", "frequencia": freq})


@app.route("/api/buscativa", methods=["GET", "POST"])
def buscativa():
    if request.method == "POST":
        dados = request.json
        dados["dataRegistro"] = datetime.now()
        colecao_buscativa.insert_one(dados)
        return jsonify({"status": "success"})
    else:
        registros = list(colecao_buscativa.find().sort("dataRegistro", -1))
        for r in registros:
            r["_id"] = str(r["_id"])
        return jsonify(registros)

@app.route("/api/limpar-alertas", methods=["DELETE"])
def limpar_alertas():
    resultado = colecao_buscativa.delete_many({
        "responsavel": "Sistema Frequência",
        "resultado": {"$regex": "Frequência abaixo"}
    })
    return jsonify({"status": "ok", "removidos": resultado.deleted_count, "message": "Alertas removidos com sucesso."})
@app.route("/api/frequencia-listar")
def listar_frequencias():
    registros = list(colecao_frequencia.find().sort("dataRegistro", -1))
    for r in registros:
        r["_id"] = str(r["_id"])
    return jsonify(registros)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
