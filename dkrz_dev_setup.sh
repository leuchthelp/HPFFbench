# Prepare your system
#sudo apt update
#sudo apt upgrade

# Install packages required by spack
#sudo apt update
#sudo apt install bzip2 ca-certificates g++ gcc gfortran git gzip lsb-release patch python3 tar unzip xz-utils zstd

# Install spack and add to local shell
git clone --depth=2 --branch=releases/v0.23.1 https://github.com/spack/spack.git ~/spack
. spack/share/spack/setup-env.sh
. $SPACK_ROOT/share/spack/setup-env.sh

# Activate creation of module files via spack
spack config add "modules:default:enable:[tcl]"

# Install and setup "module" and add to local shell
spack install lmod
. $(spack location -i lmod)/lmod/lmod/init/bash
. $SPACK_ROOT/share/spack/setup-env.sh

spack install gcc@11.4.0
spack compiler add "$(spack location -i gcc@11.4.0)"

spack install python@3.11.9 %gcc@11.4.0
spack install openmpi %gcc@11.4.0
spack install hdf5+threadsafe+mpi+subfiling %gcc@11.4.0
spack install netcdf-c build_system=cmake %gcc@11.4.0
spack install py-pip %gcc@11.4.0
spack install py-netcdf4 %gcc@11.4.0
spack install py-h5py %gcc@11.4.0
spack install py-mpi4py %gcc@11.4.0
spack install py-numpy %gcc@11.4.0
spack install py-rich %gcc@11.4.0
spack install hdf5-vol-async@develop ^argobots@main %gcc@11.4.0

# Add to end of home/user/.bashrc via nano .bashrc from within your home/user directory
#. ~/spack/share/spack/setup-env.sh
#. $SPACK_ROOT/share/spack/setup-env.sh
#. $(spack location -i lmod)/lmod/lmod/init/bash
# module load hdf5 netcdf-c py-mpi4py openmpi python py-netcdf4 py-h5py py-rich py-numpy 
# module load hdf5-vol-async/develop

# Create and enter python virtualenv and install zarr v3.0.1 as this doesnt exist in spack yet
# cd /dkrz_dev
# python -m venv .venv
# source .venv/bin/activate
# pip install -r requirements.txt

# All other packages should already be available to pip via spack / modules