#!/bin/bash
#SBATCH --mail-user=Moslem.Yazdanpanah@gmail.com
#SBATCH --mail-type=BEGIN
#SBATCH --mail-type=END
#SBATCH --mail-type=FAIL
#SBATCH --mail-type=REQUEUE
#SBATCH --mail-type=ALL
#SBATCH --job-name=ftm_BMS_fromImagenet
#SBATCH --output=%x-%j.out
#SBATCH --nodes=1
#SBATCH --gres=gpu:4
#SBATCH --ntasks-per-node=32
#SBATCH --mem=127000M
#SBATCH --time=1-00:15
#SBATCH --account=rrg-ebrahimi

nvidia-smi

module load python
source ~/env-cdfsl/bin/activate


echo "------------------------------------< Data preparation>----------------------------------"
echo "Copying the source code"
date +"%T"
cd $SLURM_TMPDIR
cp -r ~/scratch/cdfsl-benchmark .

echo "Copying the datasets"
date +"%T"
cp -r ~/scratch/CD-FSL_Datasets .


echo "creating data directories"
date +"%T"
cd cdfsl-benchmark
cd data
unzip -q $SLURM_TMPDIR/CD-FSL_Datasets/miniImagenet.zip

mkdir ChestX-Ray8 EuroSAT ISIC2018 plant-disease

cd EuroSAT
unzip ~/scratch/CD-FSL_Datasets/EuroSAT.zip
cd ..

cd ChestX-Ray8
unzip ~/scratch/CD-FSL_Datasets/ChestX-Ray8.zip
mkdir images
find . -type f -name '*.png' -print0 | xargs -0 mv -t images
cd ..

cd ISIC2018
unzip ~/scratch/CD-FSL_Datasets/ISIC2018.zip
unzip ~/scratch/CD-FSL_Datasets/ISIC2018_GroundTruth.zip
cd ..

cd plant-disease
unzip ~/scratch/CD-FSL_Datasets/plant-disease.zip

echo "----------------------------------< End of data preparation>--------------------------------"
date +"%T"
echo "--------------------------------------------------------------------------------------------"

echo "---------------------------------------<Run the program>------------------------------------"
date +"%T"
cd $SLURM_TMPDIR

cd cdfsl-benchmark
echo "********************************************************************************************"
python finetune.py --n_shot 5 --freeze_backbone --dataset EuroSAT --checkpoint_path ./checkpoint/SPM_bias/from_transfer_ImageNet_resnet18_MiniImageNet_to_EuroSAT.pth --gpu 0 &
python finetune.py --n_shot 5 --freeze_backbone --dataset CropDisease --checkpoint_path ./checkpoint/SPM_bias/from_transfer_ImageNet_resnet18_MiniImageNet_to_plant_disease.pth --gpu 1 &
python finetune.py --n_shot 5 --freeze_backbone --dataset ISIC --checkpoint_path ./checkpoint/SPM_bias/from_transfer_ImageNet_resnet18_MiniImageNet_to_ISIC2018.pth --gpu 2 &
python finetune.py --n_shot 5 --freeze_backbone --dataset ChestX --checkpoint_path ./checkpoint/SPM_bias/from_transfer_ImageNet_resnet18_MiniImageNet_to_ChestX_Ray8.pth --gpu 3 &

wait
echo "-----------------------------------<End of run the program>---------------------------------"
date +"%T"



