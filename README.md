# Live F1

[![CI pipeline](https://github.com/tamasmrton/live-f1/actions/workflows/pipeline.yml/badge.svg)](https://github.com/tamasmrton/live-f1/actions/workflows/pipeline.yml)

## Overview

Live F1 is a Python project designed to fetch and display real-time Formula 1 lap times and related data. It provides a visual representation of lap times, pit stops, and other relevant statistics for each F1 race session.

## Features

- Fetch real-time data from the OpenF1 API.
- Display lap times, pit stops, and other race statistics.
- Smoothly update the data.
- Customizable filters to analyze race data.
- Integration and unit tests to ensure the robustness of the application.

## Installation

To get started with Live F1, follow these steps:

### Prerequisites

- Python 3.11 or higher
- pip (Python package installer)

### Install dependencies

Create and activate a virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
```

Install the packages:

```bash
pip install -r requirements.txt
```

## Usage

To run the application, execute the following code:

```bash
streamlit run app.py
```
