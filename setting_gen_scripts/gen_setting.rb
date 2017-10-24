require 'json'
obj={}
obj["mics"]=[]
obj["mics"]<<{"name":"_m1","position":[0,0]}
		
obj["sources"]=[]

files=Dir.glob("./data/*.wav")
prng = Random.new(1234)

count=0
files.each_with_index{|f,i|
	1.times{|c|
		el={}
		el["name"]="s"+count.to_s
		el["file"]=f
		el["channel"]=1
		el["start_time"]=prng.rand(100)
		theta=prng.rand(2*Math::PI)
		r=prng.rand(10.0)+0.3
		el["position"]=[r*Math.cos(theta),r*Math.sin(theta)]
		el["tf_label"]="label"+File.basename(f,".wav")+".png"
		obj["sources"] << el
		count+=1
	}
}

puts JSON.pretty_generate(obj)
