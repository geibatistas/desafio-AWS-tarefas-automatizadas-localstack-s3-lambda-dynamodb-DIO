Compress-Archive `
  -Path processar_notas.py `
  -DestinationPath lambda_function.zip `
  -Force

aws lambda create-function `
  --function-name ProcessarNotasFiscais `
  --runtime python3.9 `
  --role arn:aws:iam::000000000000:role/lambda-role `
  --handler processar_notas.lambda_handler `
  --zip-file fileb://lambda_function.zip `
  --endpoint-url=http://localhost:4566
  