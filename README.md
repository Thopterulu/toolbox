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
A script to manage Clockify time entries with several features:

1. Environment Setup:
   - Requires API_KEY, WORKSPACE_ID, and USER_ID in env variables
   - Uses Europe/Paris timezone by default

2. Daily Schedule Features:
   - Creates morning schedule with random start times (9:15-9:28)
   - Automatically adds morning meetings (Standup and Planning)
   - Splits day entries to add lunch break (12:00-12:30)
   - Adds HPFO task at random time between 2-4 PM

3. Time Cleanup (using `CLOCKIFY_ACTION=remove_nights`):
   ```bash
   CLOCKIFY_ACTION=remove_nights python timerz/clockify.py
   ```
   This command will:
   - Process all entries from the last 2 weeks
   - Remove weekend entries completely
   - Remove work between 8 PM and 9 AM
   - Split entries to add lunch breaks (12:00-12:30)
   - Handle multi-day entries correctly

4. Regular Mode (default):
   ```bash
   python timerz/clockify.py
   ```
   This will run the daily schedule creation with lunch breaks.
