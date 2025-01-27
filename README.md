# toolbox
collection of tools

## Scripts Description

### PDF/FILIGRANE_GOUV.PY

This script automates the process of adding a watermark to a PDF document using the website [filigrane.beta.gouv.fr](https://filigrane.beta.gouv.fr/). It performs the following steps:
1. Prompts the user to enter the path to the folder containing the PDF file.
2. Defines the watermark text to be added to the PDF.
3. Sets up a Firefox web driver.
4. Navigates to the filigrane.beta.gouv.fr website.
5. Locates the file upload input element and uploads the PDF file.
6. Locates the text input element and enters the watermark text.
7. Locates and clicks the button to add the watermark.
8. Waits for the download link to appear and clicks it to download the watermarked PDF.
9. Closes the web browser.

### PDF/CONCAT_PDF.PY

This script merges multiple PDF files into a single PDF file using the PyPDF2 library. It performs the following steps:
1. Prompts the user to enter the path to the folder containing the PDF files.
2. Lists all PDF files in the specified folder.
3. Reads each PDF file and appends it to a list.
4. Creates a PdfFileMerger object.
5. Adds each PDF file from the list to the PdfFileMerger object.
6. Writes the merged PDF to a new file named "merged_output.pdf" in the same folder.


### timerz/clockify.py
1. Takes env keys
2. cut everyday a pause between 12 and 12:30
