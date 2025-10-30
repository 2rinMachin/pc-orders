FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY common functions/goodbye/handler.py  ${LAMBDA_TASK_ROOT}

CMD ["handler.handler"]
