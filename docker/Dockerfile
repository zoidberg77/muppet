FROM nvcr.io/nvidia/pytorch:20.12-py3

ARG DEBIAN_FRONTEND=noninteractive

WORKDIR /tmp

RUN apt-get update
RUN apt-get install git libgl1-mesa-glx -y
RUN git clone https://github.com/zoidberg77/muppet.git

WORKDIR /tmp/muppet

RUN conda env create -n py3_torch -f pytorch_training.yml python=3.8

SHELL ["conda", "run", "-n", "py3_torch", "/bin/bash", "-c"]

RUN python -m pip install -U pip
RUN pip install robustness

WORKDIR /app

CMD ["/opt/conda/envs/py3_torch/bin/python", "/app/main_template.py", "--config-file", "/app/configs/alexnet_muppet.ini"]
