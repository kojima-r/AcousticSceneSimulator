import json
import os
import sys
import numpy as np
import SimMch.simmch

f = open(sys.argv[1], 'r')
data = json.load(f)

obj={}
obj["mics"]=[]
obj["mics"].append({"name":"_m1","position":[0,0]})
obj["sources"]=[]



path='./data/'
wavfile_list={}
for filename,label in data.items():
	filepath=path+filename
	print filepath
	if not label in wavfile_list:
		wavfile_list[label]=[]
	wavfile_list[label].append(filepath)

n=6
count=0
data={}
time_line={i:0 for i in range(n)}
for i,filepaths in wavfile_list.items():
	for filepath in filepaths:
		if i<n and time_line[i]<20:
			wav_data=SimMch.simmch.read_mch_wave(filepath)
			if wav_data["duration"]>0.0:
				el={}
				el["name"]="s"+str(count)
				el["file"]=filepath
				el["channel"]=0
				st=time_line[i]
				el["start_time"]=st
				fs=wav_data["framerate"]
				nch=wav_data["nchannels"]
				st+= wav_data["duration"]+1.5
				time_line[i]=st
				theta=np.pi*i*2.0/n
				r=10.0
				el["position"]=[r*np.cos(theta),r*np.sin(theta)]
				#el["tf_label"]="label"+File.basename(f,".wav")+".png"
				obj["sources"].append(el)
				count+=1

print time_line


fp=open("setting.json", "w")
json.dump(obj, fp, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

