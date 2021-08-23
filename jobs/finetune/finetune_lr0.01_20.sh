#!/bin/bash
#SBATCH --mail-user=ar.aamer@gmail.com
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#SBATCH --mail-type=REQUEUE
#SBATCH --mail-type=ALL
#SBATCH --job-name=BMS_test_1
#SBATCH --output=%x-%j.out
#SBATCH --nodes=1
#SBATCH --gres=gpu:1
#SBATCH --ntasks-per-node=32
#SBATCH --mem=127000M
#SBATCH --time=0-05:00
#SBATCH --account=rrg-ebrahimi

nvidia-smi

module load python
source ~/py37/bin/activate


echo "------------------------------------< Data preparation>----------------------------------"
echo "Copying the source code"
date +"%T"
cd $SLURM_TMPDIR
cp -r ~/proj_cdf .

echo "Copying the datasets"
date +"%T"
cp -r ~/CDFSL_Datasets .


echo "creating data directories"
date +"%T"
cd proj_cdf
cd data
unzip -q $SLURM_TMPDIR/CDFSL_Datasets/miniImagenet.zip

mkdir EuroSAT

cd EuroSAT
unzip -q $SLURM_TMPDIR/CDFSL_Datasets/EuroSAT.zip
cd ..


echo "----------------------------------< End of data preparation>--------------------------------"
date +"%T"
echo "--------------------------------------------------------------------------------------------"

echo "---------------------------------------<Run the program>------------------------------------"
date +"%T"
cd $SLURM_TMPDIR

cd proj_cdf
echo "********************************************************************************************"

echo "1-shot"
python finetune_lr0.01_20.py --model ResNet10 --method baseline --n_shot 1 --freeze_backbone 
echo "5-shot"
python finetune_lr0.01_20.py --model ResNet10 --method baseline --n_shot 5 --freeze_backbone 
echo "20-shot"
python finetune_lr0.01_20.py --model ResNet10 --method baseline --n_shot 20 --freeze_backbone 
echo "50-shot"
python finetune_lr0.01_20.py --model ResNet10 --method baseline --n_shot 50 --freeze_backbone 


wait

echo "-----------------------------------<End of run the program>---------------------------------"
date +"%T"



