# LLM Email Client

## Overview

This project is a simple email client that allows LLMs to respond to emails using the Mistral API and IMAP/SMTP. It was built around Protonmail Bridge, which serves as the IMAP/SMTP server. The inbox is periodically checked for new emails, which are pulled into a postgres database. The emails are processed by an LLM agent, which generates a response and saves it to the database. The responses are then sent out using SMTP. 

## Setup

For now, this only works with the Mistral API. You will need to create an account and get an API key. You will also need to create an agent and grab the ID. 

1. Clone the repository locally by running `git clone https://2theo2blau/llm-email-client.git`
2. You will first need to login to Protonmail Bridge. Run `docker compose run protonmail-bridge init`, which will drop you into the protonmail bridge CLI. Run `login` and enter your credentials, and then run `info` to get the password for protonmail bridge (this is not the same as your protonmail password). Run `exit`, which should terminate the container.
3. Create a `.env` file and replace the variables with your own. You can use the `.env.example` file as a reference, you can run `cp .env.example .env` to copy it and fill in your own values.
4. Run `docker compose up --build -d` to start the application.