FROM public.ecr.aws/lambda/python:3.13

COPY requirements.txt ${LAMBDA_TASK_ROOT}
RUN pip install -r requirements.txt

COPY functions/hello/handler.py ${LAMBDA_TASK_ROOT}
COPY common ${LAMBDA_TASK_ROOT}/common

CMD ["handler.handler"]
