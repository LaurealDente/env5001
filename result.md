Résultat de l'api :

avec : uvicorn api:app --reload

puis : http://127.0.0.1:8000/energy?region=france

{"chatbots":{"region":"france","totals":{"inferences":223861,"energy_kwh":10266514.194,"carbon_gco2e":615990851.7}},"completions":{"region":"france","totals":{"inferences":22897,"energy_kwh":28939.264,"carbon_gco2e":1736355.8}},"translations":{"region":"france","totals":{"inferences":8191,"energy_kwh":14789.306,"carbon_gco2e":887358.3}}}

Test de traitement :

![alt text](images/image1.png)

test de l'interface :

![alt text](images/image2.png)