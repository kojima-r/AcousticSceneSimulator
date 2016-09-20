for f in ./org/*
do
	b=`basename $f`
	sox $f -r 16000 ./data/$b
done

