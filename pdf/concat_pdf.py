import PyPDF2
import os

# saisir le chemin du dossier contenant les fichiers PDF
path = input("Entrez le chemin du dossier contenant les fichiers PDF: ")

pdfs = []

for file in os.listdir(path):
    if file.endswith(".pdf"):
        print(file)
        pdfs.append(PyPDF2.PdfReader(os.path.join(path, file)))


# Créer un objet PdfFileMerger
merger = PyPDF2.PdfMerger()

# Ajouter les fichiers PDF à fusionner
for pdf in pdfs:
    merger.append(pdf)


# Écrire le résultat dans un nouveau fichier PDF
with open(os.path.join(path, "merged_output.pdf"), "wb") as output_file:
    merger.write(output_file)
