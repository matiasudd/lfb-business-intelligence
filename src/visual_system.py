from pathlib import Path
import json
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from IPython.display import Image
from matplotlib.patches import Rectangle
from matplotlib.ticker import PercentFormatter

THEME=json.loads((Path(__file__).parent/'visual_system.json').read_text())
def setup():
    plt.rcParams.update({'font.family':THEME['font'],'font.size':11,'text.color':THEME['ink'],
        'axes.labelcolor':THEME['ink'],'svg.fonttype':'none','figure.facecolor':'white','savefig.facecolor':'white'})
def finish(fig,name,out):
    out=Path(out);out.mkdir(exist_ok=True);fig.tight_layout()
    fig.savefig(out/(name+'.svg'));fig.savefig(out/(name+'.png'),dpi=160)
    plt.close(fig)
    return Image(filename=str(out/(name+'.png')))
def distribution(seconds,out):
    setup();fig,ax=plt.subplots(figsize=(9,3.7));edges=np.arange(0,1320,120)
    n,_,bars=ax.hist(seconds,bins=edges,color=THEME['model'],edgecolor='white')
    for i,b in enumerate(bars):
        if edges[i]>=600:b.set_facecolor(THEME['attention'])
    ax.set(title='Observed dispatch-to-arrival times, 2023–2024',xlabel='Seconds from dispatch to arrival',ylabel='Vehicle dispatches')
    ax.text(.98,.96,f'n = {len(seconds):,}',ha='right',va='top',transform=ax.transAxes)
    return finish(fig,'01_distribution',out)
def comparison(labels,values,title,name,out):
    setup();fig,ax=plt.subplots(figsize=(8.5,3.4));y=np.arange(len(labels));ax.barh(y,values,color=THEME['model']);ax.set_yticks(y,labels);ax.invert_yaxis()
    ax.set(title=title,xlabel='Share taking at least 600 seconds (%)',xlim=(0,16));ax.grid(axis='x',alpha=.18);ax.set_axisbelow(True)
    for i,v in enumerate(values):ax.text(v+.15,i,f'{v:.2f}%',va='center')
    return finish(fig,name,out)
def composition(after,out):
    setup();fig,ax=plt.subplots(figsize=(8.5,3.8));long=np.array([6.702,6.712,7.270]);short=100-long;y=np.arange(3)
    if after:ax.barh(y,long,color=THEME['attention']);ax.barh(y,short,left=long,color=THEME['context'])
    else:ax.barh(y-.17,long,height=.3,color=THEME['attention']);ax.barh(y+.17,short,height=.3,color=THEME['context'])
    ax.set_yticks(y,['Training','Validation','Test']);ax.invert_yaxis();ax.set(xlim=(0,100),xlabel='Share of eligible dispatches (%)',title='Composition of the original C2 partitions')
    for i,v in enumerate(long):ax.text(v+1,i if after else i-.17,f'{v:.3f}%',va='center',color=THEME['attention'])
    ax.xaxis.set_major_formatter(PercentFormatter(100));ax.text(0,-.22,'Training 186,339   Validation 96,040   Test 102,248',transform=ax.transAxes,fontsize=10)
    return finish(fig,'w3_composition_'+('after' if after else 'before'),out)
def metrics(after,out):
    setup();fig,ax=plt.subplots(figsize=(8.5,4));base=np.array([92.73,0,0,0]);model=np.array([53.70,9.39,62.06,16.31]);y=np.arange(4)
    if after:
        for i,a,b in zip(y,base,model):ax.plot([a,b],[i,i],color=THEME['context'],lw=2)
        ax.scatter(base,y,c=THEME['reference'],marker='s',label='Reference');ax.scatter(model,y,c=THEME['model'],label='Hour-only logistic')
        ax.scatter(model[2],y[2],s=145,facecolors='none',edgecolors=THEME['attention'],linewidths=2)
    else:ax.barh(y-.17,base,height=.3,color=THEME['reference'],label='Reference');ax.barh(y+.17,model,height=.3,color=THEME['model'],label='Hour-only logistic')
    ax.set_yticks(y,['Accuracy','Precision*','Recall','F1']);ax.invert_yaxis();ax.set(xlim=(-2,103),xlabel='Test score (%)',title='Original C2 model and its always-short reference')
    ax.legend(loc='lower right');ax.text(0,-.22,'*Reference precision undefined with no alerts; C2 stored zero.',transform=ax.transAxes,fontsize=9)
    return finish(fig,'w3_metrics_'+('after' if after else 'before'),out)
def confusion(after,out,final=False):
    setup();fig,ax=plt.subplots(figsize=(7,4.6));a=np.array([[61264,33551],[988,6445]]) if final else np.array([[50298,44517],[2820,4613]])
    ax.imshow(a,cmap='Blues' if after else 'Greys',vmin=0,vmax=80000)
    labels=[['Correct short','False alert'],['Missed long','Detected long']]
    for r in range(2):
        for c in range(2):
            col='white' if a[r,c]>40000 else THEME['ink'];s=f'{a[r,c]:,}'
            if after:s+='\n'+labels[r][c]
            ax.text(c,r,s,ha='center',va='center',color=col,fontsize=14)
    if after:ax.add_patch(Rectangle((-.5,.5),1,1,fill=False,edgecolor=THEME['attention'],lw=4))
    ax.set_xticks([0,1],['Predicted under 10 min','Predicted at least 10 min']);ax.set_yticks([0,1],['Actual under 10 min','Actual at least 10 min'])
    ax.set_title('Final selected model' if final else 'Original C2 errors, n = 102,248')
    return finish(fig,'final_confusion' if final else 'w3_errors_'+('after' if after else 'before'),out)
