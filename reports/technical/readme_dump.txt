Download Link   |
|--------------|---------------|---------|-------------------------------------------|--------------|
| **Phish360 (ours)** | ~11k | Parquet Files    | 0.6 GB | [Download](https://drive.google.com/drive/u/1/folders/1ulQYtb63pZlhgcKMuTeiDze1onsY1yKT)  |
| PWD2016       | 30k | Parquet Files    |  1.1 GB | [Download](https://drive.google.com/drive/folders/1IWip7RW_p8iISYMAT-Db_pFIp4BWb_sn?usp=drive_link)  |
| PhishIntention | ~58k | Parquet Files    | 2.5 GB | [Download](https://drive.google.com/drive/folders/1VsApDC3kYFu7HJ2joYN-klG4jIvOQLkQ?usp=drive_link) | 
| VanNL126k | ~126k| Parquet Files    |  5.12 GB | [Download](https://drive.google.com/drive/folders/1JzcYGREyEewglE-uWWZqdQA8Sz0iBiWh?usp=drive_link) |
| PILWD-134K | ~134k | Parquet Files    |  8.36 GB | [Download](https://drive.google.com/drive/u/2/folders/1TYwUehoq4pFGYnvn8iXQqtSbS788mgLi)  |

## Repository Structure
```
Multimodal-Phishing-Benchmarks/
├── notebooks/
│   ├── individual/           # Individual dataset EDA notebooks
│   │   ├── Phish360 EDA PQ.ipynb
│   │   ├── PWD2016 EDA PQ.ipynb
│   │   ├── PhishIntention EDA PQ.ipynb
│   │   ├── PILWD-134K EDA PQ.ipynb
│   │   └── VanNL126k EDA PQ.ipynb
│   └── comparative/          # Cross-dataset comparison
│       └── Comparative_Analysis.ipynb
├── scripts/                  # Reproducibility: metric generation code
│   └── comprehensive_analysis.py  # Generates all plots and metrics
├── results/
│   ├── plots/               # Generated visualizations (6 plots)
│   └── metrics/             # Metric CSV files (6 files)
└── README.md
```

> **📌 Note on Scripts:** The `scripts/` folder contains the source code used to generate all metrics and visualizations in `results/`. This ensures **reproducibility** - researchers can verify our methodology and regenerate results independently.

## Notebooks
1. **Individual Dataset EDAs:**
   - [Phish360 EDA](notebooks/individual/Phish360%20EDA%20PQ.ipynb)
   - [PWD2016 EDA](notebooks/individual/PWD2016%20EDA%20PQ.ipynb)
   - [PhishIntention EDA](notebooks/individual/PhishIntention%20EDA%20PQ.ipynb)
   - [VanNL126k EDA](notebooks/individual/VanNL126k%20EDA%20PQ.ipynb)
   - [PILWD-134K EDA](notebooks/individual/PILWD-134K%20EDA%20PQ.ipynb)

2. **Comparative Analysis:**
   - [Comprehensive Benchmarking](notebooks/comparative/Comparative_Analysis.ipynb) *(7-dimensional quality assessment)*

## Contact Information

- **Email:** almakhamrehahmad@gmail.com
- **LinkedIn:** [https://www.linkedin.com/in/ahmadalmakhamreh/](https://www.linkedin.com/in/ahmadalmakhamreh/)
- **GitHub:** [https://github.com/almakhamreh](https://github.com/almakhamreh)

## References

Here are some useful resources for further reading:

- [PWD2016](https://www.researchgate.net/profile/Colin-Choon-Lin-Tan/publication/329554848_Building_Standard_Offline_Anti-phishing_Dataset_for_Benchmarking/links/5c0f24374585157ac1b9194e/Building-Standard-Offline-Anti-phishing-Dataset-for-Benchmarking.pdf): In depth description abo