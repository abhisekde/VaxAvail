# VaxAvail
A telegram messenger based chatbot to help people find available vaccination appointment slots for #covid19india.

## Requirements (python modules)
- pyTelegramBotAPI
- boto3 

## Architecture
This app is designed to run on AWS infrastructures. If you wish to run or test locally then perform the following edits or set up similar infrastructure in AWS 
1. Create a bot first. Speak to BotFather at https://t.me/botfather to set up your chatbot and safely store your telegram bot API token.
2. Credentials for bot API is securely fetched from AWS Secrets manager in`secrets.py`, initate the variable `TOKEN` locally. This is the API token for telegram bot. 
3. Update the methods inside `dynamo.py` to use your own document based database (eg mongodb).
4. All bot interactions are stored in `talk.py`, to change dialogue modify the dialogues dictionary

## Execution
There are two parts to this system
- Chatbot: `bot.py`
- Core logic: `core.py`

### Chatbot
The interaction with the user is mainly handled by the chatbot module and can be executed as 
`python3 bot.py` 

### Core logic
The is the heart of the system which checks for the available vaccination slots from the CoWIN API end points and informs back the users in case slots are available for them. Execute as `python3 core.py`

Please read Telegram bot API https://core.telegram.org/bots/api and pyTelegramBotAPI https://github.com/eternnoir/pyTelegramBotAPI documentation for more details.
