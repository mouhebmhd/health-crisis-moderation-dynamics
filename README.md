# Health Crisis Moderation Dynamics

## 📋 Project Overview
This research project investigates the **co-evolutionary dynamics** between health misinformation and community moderation rules within online platforms during public health crises (e.g., COVID-19, Ebola, Mpox). Using temporal analysis, we examine how moderation policies adapt in response to emerging misinformation narratives and how, in turn, those narratives mutate to circumvent new rules.

## 🎯 Research Questions
1. How do moderation rules in online health communities change in response to specific misinformation surges during a crisis?
2. How does misinformation content and dissemination strategy evolve in reaction to updated moderation policies?
3. What patterns of co-evolution (e.g., arms race, adaptive cycles) characterize this relationship over time?

## 🗂️ Repository Structure
health-crisis-moderation-dynamics/
│
├── data/ # Project data (anonymized/processed)
│ ├── raw/ # Raw datasets (not tracked in Git)
│ ├── processed/ # Cleaned and structured data
│ └── metadata/ # Codebooks and collection notes
│
├── src/ # Source code & analysis scripts
│ ├── 01_data_collection/
│ ├── 02_preprocessing/
│ ├── 03_analysis/
│ └── 04_visualization/
│
├── notebooks/ # Jupyter/R Markdown notebooks for exploratory analysis
├── outputs/ # Generated figures, tables, and model results
├── docs/ # Project documentation, literature, and protocols
├── paper/ # Manuscript source (LaTeX/Word), drafts, and supplements
└── README.md # This file

## 🛠️ Methodology & Tools
- **Data Sources:** Reddit/Forum archives (via Pushshift/API), platform transparency reports, moderation logs
- **Temporal Analysis:** Change point detection, sequence analysis, time-series modeling
- **Text Analysis:** NLP for misinformation classification (BERT, topic modeling), rule parsing
- **Network Analysis:** Co-evolution networks of narratives vs. rules
- **Primary Tools:* Python (pandas, NetworkX, transformers), R (tidyverse, tsibble), Git
## 🚀 Clone the repository
   ```bash
   git clone https://github.com/[your-username]/health-crisis-moderation-dynamics.git
   cd health-crisis-moderation-dynamics
