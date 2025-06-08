helm repo add elastic https://helm.elastic.co
helm repo update

kubectl create namespace elk

helm upgrade --install elasticsearch elastic/elasticsearch -n elk -f .\elasticsearch\elasticsearch.yaml
kubectl scale statefulsets elasticsearch-master --replicas=2

helm upgrade --install kibana elastic/kibana -n elk -f .\kibana\kibana.yaml
helm upgrade --install logstash elastic/logstash -n elk -f .\logstash\logstash.yaml
helm upgrade --install apm-server elastic/apm-server -n elk -f .\apm-server\apm-server.yaml