\# Kingshot Governor Gear Optimizer



A simple Streamlit app to find the best upgrades for your Governor Gear in \*\*Kingshot\*\*.



\## Features



\- Enter your \*\*current gear\*\* and \*\*inventory\*\* (Satin, Threads, Artisans)  

\- Automatically calculates \*\*best upgrades\*\* using Pareto optimization  

\- Shows \*\*KVK Points\*\*, \*\*Gain (%)\*\*, and normalized `% of Max` values  

\- Highlights the \*\*best KVK Points\*\* and \*\*best Gain\*\* in the table  

\- Save / Load your \*\*current gear\*\* as JSON  



\## Installation



1\. Clone the repository:



```bash

git clone <repo\_url>

cd ks\_gov\_gear



2\. Create a virtual environment (optional but recommended):



python -m venv venv

source venv/bin/activate   # Linux/Mac

venv\\Scripts\\activate      # Windows



3\. Install dependencies:



pip install -r requirements.txt

Usage



4\. Run the Streamlit app locally:



streamlit run app.py



Set your current gear and inventory



Click "Calculate Best Upgrades"



View the Pareto-optimal upgrades in the table



Save your gear to a JSON file if needed



Files



app.py → Main Streamlit application



utils\_gov\_gear.py → Gear calculation engine



data/gear\_levels.json → Gear upgrade costs and stats



gear.json → Optional: save/load your current gear



Notes



The table highlights the best KVK Points (blue) and best Gain (%) (orange).



KVK Points are multiplied by 36 for display.



Large inventories may produce many upgrade combinations, so initial calculations can take a few seconds.

