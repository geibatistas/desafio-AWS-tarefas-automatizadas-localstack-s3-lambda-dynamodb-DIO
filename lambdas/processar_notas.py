import json
import boto3

from decimal import Decimal
from datetime import datetime

# Para LocalStack
s3 = boto3.client(
    "s3",
    endpoint_url="http://host.docker.internal:4566",
    region_name="us-east-1"
)

dynamodb = boto3.resource(
    "dynamodb",
    endpoint_url="http://host.docker.internal:4566",
    region_name="us-east-1"
)

table = dynamodb.Table("NotasFiscais")


def validar(item):

    campos_obrigatorios = [
        "id",
        "cliente",
        "valor",
        "data_emissao"
    ]

    for campo in campos_obrigatorios:

        if campo not in item:
            raise Exception(
                f"Campo obrigatório ausente: {campo}"
            )

    return True


def mover_arquivo(bucket, origem, destino):

    s3.copy_object(
        Bucket=bucket,
        CopySource={
            "Bucket": bucket,
            "Key": origem
        },
        Key=destino
    )

    s3.delete_object(
        Bucket=bucket,
        Key=origem
    )


def gerar_nome(destino, nome_original):

    timestamp = datetime.now().strftime(
        "%Y%m%d%H%M%S"
    )

    return f"{destino}/{timestamp}_{nome_original}"


def lambda_handler(event, context):

    print("Evento recebido:")
    print(json.dumps(event))

    record = event["Records"][0]

    bucket = record["s3"]["bucket"]["name"]
    key = record["s3"]["object"]["key"]

    print(f"Bucket: {bucket}")
    print(f"Arquivo: {key}")

    # Evita loop infinito
    if key.startswith("sucesso/"):
        print("Arquivo já processado com sucesso.")
        return {
            "statusCode": 200,
            "body": "Ignorado"
        }

    if key.startswith("erro/"):
        print("Arquivo já processado com erro.")
        return {
            "statusCode": 200,
            "body": "Ignorado"
        }

    # Processa apenas JSON
    if not key.endswith(".json"):
        print("Arquivo ignorado. Não é JSON.")
        return {
            "statusCode": 200,
            "body": "Arquivo ignorado"
        }

    try:

        response = s3.get_object(
            Bucket=bucket,
            Key=key
        )

        conteudo = response["Body"].read().decode(
            "utf-8"
        )

        dados = json.loads(
            conteudo,
            parse_float=Decimal
        )

        if isinstance(dados, list):

            for item in dados:

                validar(item)

                table.put_item(
                    Item=item
                )

        else:

            validar(dados)

            table.put_item(
                Item=dados
            )

        novo_nome = gerar_nome(
            "sucesso",
            key.split("/")[-1]
        )

        mover_arquivo(
            bucket,
            key,
            novo_nome
        )

        print(
            f"Arquivo movido para {novo_nome}"
        )

        return {
            "statusCode": 200,
            "body": json.dumps(
                "Arquivo processado com sucesso."
            )
        }

    except Exception as e:

        print(f"ERRO: {str(e)}")

        try:

            novo_nome = gerar_nome(
                "erro",
                key.split("/")[-1]
            )

            mover_arquivo(
                bucket,
                key,
                novo_nome
            )

            print(
                f"Arquivo movido para {novo_nome}"
            )

        except Exception as erro_movimentacao:

            print(
                f"Falha ao mover arquivo para pasta erro: "
                f"{str(erro_movimentacao)}"
            )

        raise e
