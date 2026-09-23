from pathlib import Path
import json
import pandas as pd
import numpy as np
ROOT=Path(__file__).resolve().parents[1]
clean=pd.read_csv(ROOT/'data/processed/mobilisations_2023_2024_clean.csv')
values=clean.attendance_min.to_numpy()
counts,edges=np.histogram(values,bins=np.arange(0,21,1))
from scipy.stats import gaussian_kde
sample=np.random.default_rng(423).choice(values,min(20000,len(values)),replace=False)
grid=np.linspace(0,20,41)
kde=gaussian_kde(sample)
data={'summary':json.loads((ROOT/'outputs/summary.json').read_text()),
      'audit':json.loads((ROOT/'outputs/audit.json').read_text()),
      'histogram':{'categories':[f'{int(x)}-{int(x+1)}' for x in edges[:-1]],'values':counts.tolist()},
      'density':{'categories':[str(x) for x in grid],'values':(kde(grid)+kde(-grid)).tolist()}}
for name in ['monthly','borough','hour','year']:
    data[name]=pd.read_csv(ROOT/f'outputs/{name}_metrics.csv').to_dict(orient='records')
data['correlations']=pd.read_csv(ROOT/'outputs/spearman_components.csv',index_col=0).to_dict()
(ROOT/'outputs/deck_data.json').write_text(json.dumps(data,indent=2))
