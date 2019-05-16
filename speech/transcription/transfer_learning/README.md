# Importers for DeepSpeech

Contains importers for ECC calls made on the system, does the following:
* Fetches all the calls made using sql connects with the system, takes the SQL password from the command line
* Performs VAD on the calls to generate snippets
* Transcribes these snippets and stores the raw values in a db
* Exposes the snippets and files using a server to perform QA on the snippets
* Extracts the snippets whose QA has been performed to the DeepSpeech compatible format and splits into dev-test-train
