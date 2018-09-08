# 2d
rm data_sim/*.wav
uid=`basename $1 .json`
python -u build_sim_dataset.py ${1} --zip --id $uid > log.txt
#zip -r ./static/data_sim.zip data_sim

#echo "aaa" > log.txt
#for i in `seq 5`
#do
#	echo "aaa" >> log.txt
#	sleep 1
#done
# 3d
#python build_sim_dataset_3d.py tf/dacho_geotf_3d.zip
#mv data_sim_3d/*.wav ./
