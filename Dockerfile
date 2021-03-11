FROM nvcr.io/nvidia/pytorch:20.12-py3


WORKDIR /app
COPY . .

RUN apt-get update
RUN apt-get install libgl1-mesa-glx -y
RUN python -m pip install -U pip
RUN pip install -r requirements.txt

CMD ["python", "main_template.py", "--config-file", "configs/alexnet_muppet.ini"]