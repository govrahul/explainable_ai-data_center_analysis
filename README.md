# Data Center Analysis

This project is for AIPI 590: Explainable AI at Duke University.

## Requirements and Setup

Ensure you have Python installed. Install the packages necessary for this project using:
```bash
pip install -r requirements.txt
```

Next, create a .env file in the root directory and create these two free API keys:
- ```EIA_API_KEY```: https://www.eia.gov/opendata/register.php
- ```CENSUS_API_KEY```: https://api.census.gov/data/key_signup.html

## Data Loading
To load all necessary data, first ensure your API keys have been created. Then, simply run:
```bash
python Data/load_facilities_data.py
python Data/load_eia_data.py
python Data/load_water_data.py
python Data/load_acs_data.py
```

## Published Website
To view the final website, including an interactive map, please visit https://explainableai-datacenteranalysis.streamlit.app/.

<sub>Created by [Rahul Govil](https://linkedin.com/in/govrahul)