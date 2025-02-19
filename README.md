# LLM Email Client

## Overview

This project is a simple email client that allows LLMs to respond to emails using the Mistral API and IMAP/SMTP. It was built around Protonmail Bridge, which serves as the IMAP/SMTP server. The inbox is periodically checked for new emails, which are pulled into a postgres database. The emails are then processed by an LLM agent, which generates a response and saves it to the database. The responses are then sent out using SMTP. 