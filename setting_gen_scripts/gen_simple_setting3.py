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

m=3
n=6
l=10
count=0
time_line0={i:0 for i in range(n)}
for i,filepaths in wavfile_list.items():
	for filepath in filepaths:
		if i<n and time_line0[i]<l:
			wav_data=SimMch.simmch.read_mch_wave(filepath)
			if wav_data["duration"]>1.0:
				st=time_line0[i]
				st+= wav_data["duration"]-1.0
				time_line0[i]=st
			else:
				st=time_line0[i]
				st+= wav_data["duration"]+1.5
				time_line0[i]=st
step=max([t for i,t in time_line0.items()])
step+=1.5

print time_line0
data={}
time_line={i:0 for i in range(n)}
for i,filepaths in wavfile_list.items():
	for filepath in filepaths:
		if i<n and time_line[i]<l:
			wav_data=SimMch.simmch.read_mch_wave(filepath)
			el={}
			el["name"]="s"+str(count)
			el["file"]=filepath
			el["channel"]=0
			st=time_line[i]
			el["start_time"]=st+step*(i/m)
			fs=wav_data["framerate"]
			nch=wav_data["nchannels"]
			if wav_data["duration"]>1.0:
				st+= wav_data["duration"]-1.0
				time_line[i]=st
			else:
				st+= wav_data["duration"]+1.5
				time_line[i]=st
			theta=np.pi*(i%m)*2.0/m+(count%3-1)*4*np.pi/36.0
			r=10.0
			el["position"]=[r*np.cos(theta),r*np.sin(theta)]
			#el["tf_label"]="label"+File.basename(f,".wav")+".png"
			obj["sources"].append(el)
			count+=1


fp=open("setting.json", "w")
json.dump(obj, fp, ensure_ascii=False, indent=4, sort_keys=True, separators=(',', ': '))

