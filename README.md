# GPU topology-aware scheduler

- Hardware dependencies:

The system relies on NVIDIA 1 GPUs and commands for topology discovering and metrics collection. Some PMU events code are specific to Power8
architecture, whose the documentation is public available in IBM official website. Additionally, it is necessary that
P2P capabilities are enabled in the BIOS.

- Software dependencies:

Caffe is public available in https://github.com/BVLC/caffe and the library perfmon2 in
http://perfmon2.sourceforge.net/. All the benchmarks used for the experiments are available in the caffe source code
and requires no modification except from changing the training batch size.

- Experiment workflow:

The system can run in the simulation mode or as a real prototype based on predefined configuration file etc/configs/sys-config.ini,
changing the parameter simulation to True or False. When the simulation is false, the system will run jobs accordingly to user-defined
bash script file (workload manifest), which receives the jobs and runtime (e.g. GPU Ids) information and translate it to a command
to execute a Caffe instance.

There is also a workload generator, which receives as parameters the arrival rate and probabilities of batch size, the amount of GPUs
and workload type as described in the paper. Each scheduler algorithm also has a configuration file
etc/configs/algo-name-config.ini, which must be provide from at least one algorithm. If many are provided, the system will
execute multiples runs configured with different schedule algorithm.

After providing the needed configuration files and workload manifests, to execute the system is only required to run the main
file as ‘python main.py‘. Samples of all configuration files and workload manifest are provided in the source code.
The figures generated for the experiment section in the paper were provided from the scripts in the src/plot/*.
