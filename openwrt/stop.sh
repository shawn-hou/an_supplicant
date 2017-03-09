echo "stoping edu_supplicant_py..."
PID=`ps | grep 'edu_supplicant_py' | grep -v 'grep' | awk '{print $1}'`
if [ "" != "$PID" ]; then
  echo "killing $PID"
  kill -9 $PID
fi
echo "edu_supplicant_py stoped!"
