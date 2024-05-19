#! /bin/bash
#SBATCH --job-name="t5_vvvorobinov"
#SBATCH --gpus=2
#SBATCH --nodes=1
#SBATCH --cpus-per-task=8
#SBATCH --time=0-16:0
#SBATCH --mail-user=vvvorobinov@edu.hse.ru
#SBATCH --mail-type=ALL
#SBATCH --output="log"%j.out
#SBATCH --error="error"%j.out
#SBATCH --constraint="type_a|type_b|type_c"


module purge
module load Python
source deactivate
source activate t5_env

nvidia-smi	
which python
python -V
python -c 'import torch; print(torch.cuda.is_available())'

python3 -u main.py
