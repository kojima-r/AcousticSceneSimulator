from SimMch.make_noise import make_white_noise
from SimMch.sim_tf import apply_tf
import SimMch.simmch
from SimMch.HARK_TF_Parser.read_mat import read_hark_tf
from SimMch.HARK_TF_Parser.read_param import read_hark_tf_param
from scipy import hamming
import os
import os.path
import sys
import numpy as np
import json
import math
import argparse
from PIL import Image
import zipfile
import glob

out_tf_label_flag=False

def to_img(array):
	return Image.fromarray(np.uint8(array))
def from_img(img):
	arr = np.asarray(img)
	arr.flags.writeable = True
	return arr
def loadImgMat(filename):
	img = Image.open(filename)
	return from_img(img)
def saveImgMat(filename,mat):
	l=np.min(mat)
	h=np.max(mat)
	img=to_img((1.0-(mat-l)/h)*255)
	img.save(filename)

def load_label(filename,mapping):
	label=loadImgMat(filename)
	print("[load]",filename)
	ret_label=np.zeros((label.shape[0],label.shape[1]))
	for i in range(label.shape[0]):
		for j in range(label.shape[1]):
			k=tuple(label[i,j].tolist()[0:3]) 
			if not k in mapping:
				v=len(mapping)
				mapping[k]=v
				ret_label[i,j]=v
			else:
				v=mapping[k]
				ret_label[i,j]=v
	return np.flipud(ret_label)

def save_spectrogram(filename,wav,fftLen,step):
	win = hamming(fftLen)
	spec=SimMch.simmch.stft(wav,win,step)
	x=(np.absolute(spec[:,:spec.shape[1]/2+1].T))
	print("[INFO]",x.shape)
	print("[save]",filename)
	saveImgMat(filename,np.flipud(x))

def label_merge(org_mat,mat):
	conflict_cnt=0
	#for i in xrange(mat.shape[0]):
		#	for j in xrange(mat.shape[1]):
	for i in range(org_mat.shape[0]):
		for j in range(org_mat.shape[1]):
			if org_mat[i,j]==0:
				org_mat[i,j]=mat[i,j]
			else:
				conflict_cnt+=1
	if conflict_cnt>0:
		print("label conflict (count=%d)"%(conflict_cnt))

if __name__ == "__main__":
	parser = argparse.ArgumentParser()
	parser.add_argument('setting', type=str,
			help='setting file')
	parser.add_argument('--alpha', type=float,
			default=0.1,
			help='environmental noise rate')
	parser.add_argument('--tf', type=float,
			default=None,
			help='default tf file')
	parser.add_argument('--zip',
			action='store_true',
			help='')
	parser.add_argument('--id', type=str,
			default=None,
			help='id for output file')

	args=parser.parse_args()
	# config

	dataset_config={}
	## basic config
	fftLen = 512
	step = fftLen/4
	scale=32767.0
	output_dir="data_sim/"
	output_label_dir="label/"
	deg_step=30
	alpha=args.alpha
	setting_filename=args.setting
	f = open(setting_filename)
	data = json.load(f)
	if "noise" in data["env"]:
		alpha=data["env"]["noise"]
	enabled_wav_save=False
	## read tf 
	if args.tf is not None:
		tf_filename=args.tf
		print("... reading", tf_filename)
		tf_default_config=read_hark_tf(tf_filename)
	else:
		tf_default_config=None
	#mic_pos=read_hark_tf_param(tf_filename)
	#print "# mic positions  :",mic_pos
	
	dataset_wavname=[]
	dataset_wav=[]
	dataset_deg=[]
	label_mapping={(0, 0, 0): 0}
	for mic in data["mics"]:
		if "tf" in mic:
			tf_filename=mic["tf"]
			print("... reading", tf_filename)
			tf_config=read_hark_tf(tf_filename)
		else:
			tf_config=tf_default_config
		recorded_wav=[]
		recorded_label=[]
		for src in data["sources"]:
			m=np.array(mic["position"])
			s=np.array(src["position"])
			ch=0
			if "channel" in src:
				ch=int(src["channel"])
			start_time_sec=0
			if "start_time" in src:
				start_time_sec=float(src["start_time"])
			v = s-m
			theta=np.arctan2(v[1],v[0])-math.pi/2.0
			r= np.linalg.norm(m-s)
			print("start_time=",start_time_sec)
			print("r=",r)
			print("theta=",theta)
			wav_filename=src["file"]
			## read wav file
			print("... reading", wav_filename)
			wav_data=SimMch.simmch.read_mch_wave(wav_filename)
			wav=wav_data["wav"]/scale
			fs=wav_data["framerate"]
			nch=wav_data["nchannels"]
			step_sec=step*1.0/fs
			if ch >= wav.shape[0]:
				print("Error: ch=%d is out of range"%(ch), file=sys.stderr)
				quit()
			mono_wavdata = wav[ch,:]
			src_theta=theta
			## apply TF
			src_index=SimMch.simmch.nearest_direction_index(tf_config,src_theta)
			print("... applying tf (theta,index)=(%f,%d)"%(src_theta,src_index))
			if not src_index in tf_config["tf"]:
				print("Error: tf index",src_index,"does not exist in TF file", file=sys.stderr)
				quit()
			
			mch_wavdata=apply_tf(mono_wavdata,fftLen, step,tf_config,src_index)
			a=np.max(mch_wavdata)
			mch_wavdata=mch_wavdata/a
			print("# simulation: %s, direction of arrival: %f"%(wav_filename,theta))
			#
			print("# wav data :",mch_wavdata.shape)
			#padding_length=int(np.round(start_time_sec/step_sec))
			padding_length=int(np.round(start_time_sec*fs))
			print("# padding samples: ",padding_length)
			padding=np.zeros((mch_wavdata.shape[0],padding_length),dtype='float')
			#mch_wavdata_with_padding=np.c_[mch_wavdata,padding]
			mch_wavdata_with_padding=np.c_[padding,mch_wavdata]
			#
			recorded_wav.append(mch_wavdata_with_padding)
			## load label & save spectrogram
			label_mat=None
			if "tf_label" in src and out_tf_label_flag:
				filename=output_dir+src["tf_label"]
				save_spectrogram(filename,mono_wavdata,fftLen,step)
				filename=output_label_dir+src["tf_label"]
				if os.path.exists(filename):
					label_mat=load_label(filename,label_mapping).T
					recorded_label.append((src_theta,padding_length,label_mat))
		##
		if(len(recorded_wav)>0):
			nch=recorded_wav[0].shape[0]
			wav_len=np.max([x.shape[1] for x in recorded_wav])
			mix_wavdata=np.zeros((nch,wav_len),dtype="float")
			for w in recorded_wav:
				l=w.shape[1]
				mix_wavdata[:,:l]+=w
			a=np.max(mix_wavdata)
			mix_wavdata=mix_wavdata/a
			### make noise
			nsamples=wav_len
			length=((nsamples-(fftLen-step))-1)/step+1
			mch_noise=make_white_noise(nch,length,fftLen,step)
			a=np.max(mch_noise)
			mch_noise=mch_noise/a
			## mix noise and m-ch wav
			mix_wavdata=mix_wavdata*(1-alpha)+mch_noise[:,:wav_len]*alpha
			### make label data
			if len(recorded_label)>0:
				dir_num=len(list(tf_config["tf"].items()))
				label_data=np.zeros((length,dir_num,fftLen/2+1))
				for src_theta,pad,mat in recorded_label:
					d=10.0/180.0*math.pi
					dir_indeces=SimMch.simmch.range_direction_index(tf_config,src_theta,d)
					pad_length=((pad-(fftLen-step))-1)/step+1
					for index in dir_indeces:
						#label_data[pad_length:pad_length+mat.shape[0],index,:]+=mat
						label_merge(label_data[pad_length:pad_length+mat.shape[0],index,:],mat)

				print("# label data :",label_data.shape)
				print("# labeled elements :%d/%d"%(np.count_nonzero(label_data),np.prod(label_data.shape)))
				output_label_filename=output_label_dir+"label"+mic["name"]+".npy"
				np.save(output_label_filename,label_data)
				print("[SAVE]",output_label_filename)
			## save
			output_filename="./data_sim/"+mic["name"]+".wav"
			print("[SAVE]",output_filename)
			SimMch.simmch.save_mch_wave(mix_wavdata*scale,output_filename)	
	###
	print(label_mapping)
	inv_label_mapping={}
	for k,v in list(label_mapping.items()):
		inv_label_mapping[v]=k

	output_label_mapping=output_label_dir+"label_mapping.json"
	fp = open(output_label_mapping,"w")
	json.dump(inv_label_mapping, fp)
	print("[SAVE]",output_label_mapping)
	###
	if args.zip:
		output_filename="static/data_sim.zip"
		arc_path="data_sim/"
		if args.id:
			output_filename='static/'+args.id+".zip"
			arc_path=args.id+"/"
		
		with zipfile.ZipFile(output_filename, 'w', compression=zipfile.ZIP_DEFLATED) as new_zip:
			for el in glob.glob("data_sim/*"):
				name=os.path.basename(el)
				new_zip.write(el,arcname=arc_path+name)
				
