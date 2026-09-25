
# CareFlow AI

## AI-Powered Hospital Appointment Management

CareFlow AI is an independent healthcare AI engineering
portfolio project built using Python, Streamlit, SQLite,
and the OpenAI API.

## Problem

Hospital scheduling teams need to identify upcoming
appointments that have not yet been confirmed and
prepare appropriate confirmation reminders.

## Solution

CareFlow AI provides an appointment management dashboard
that identifies unconfirmed appointments within a
24-hour follow-up window and generates reminder drafts
using Generative AI.

## Features

- Appointment registration
- SQLite database integration
- Automatic appointment follow-up checks
- AI-generated reminder drafts
- Confirmation status management
- Interactive scheduling dashboard

## Technologies

Python, Streamlit, SQLite, OpenAI API, Generative AI

## Run Locally

1. Install Python.
2. Install the libraries in requirements.txt.
3. Optionally configure an OpenAI API key in .env.
4. Run:

   python -m streamlit run app.py

5. Click "Load three fictional appointments"
   to create sample data.

## Important

This project uses fictional appointment data.

It is not connected to a real hospital,
does not send patient notifications,
and does not make medical decisions.