with open('docs/index.html', 'r') as f:
    html = f.read()

search = "else{\n                Plotly.newPlot('customChart',[{\n                    type:'scatter',\n                    mode:'lines+markers'"

bubble = "else if(chartType==='bubble'){\n                const bubbleData=srt.map(([label,value])=>{const count=grp[label]?grp[label].length:0;return {label:label,y:parseFloat(value)||0,size:count};});\n                Plotly.newPlot('customChart',[{type:'scatter',mode:'markers',x:bubbleData.map(d=>d.label),y:bubbleData.map(d=>d.y),marker:{size:bubbleData.map(d=>d.size),sizemode:'area',sizeref:2.0*Math.max(...bubbleData.map(d=>d.size))/(40**2),sizemin:4,color:colors.terra,opacity:0.7,line:{color:'white',width:2}},text:bubbleData.map(d=>d.label+'<br>'+d.y.toLocaleString()+'<br>'+d.size+' patients'),hovertemplate:'%{text}<extra></extra>'}],{font:{family:'Inter',size:11,color:'#2d2d2d'},paper_bgcolor:'white',plot_bgcolor:'white',margin:{t:20,b:120,l:60,r:20},height:400,xaxis:{title:'',gridcolor:'#f5f5f5',tickangle:-45},yaxis:{title:metricNames[metric],gridcolor:'#f5f5f5'}},plotlyConfig);}\n            else{\n                Plotly.newPlot('customChart',[{\n                    type:'scatter',\n                    mode:'lines+markers'"

if search in html:
    html = html.replace(search, bubble)
    with open('docs/index.html', 'w') as f:
        f.write(html)
    print("Fixed!")
else:
    print("Not found")
