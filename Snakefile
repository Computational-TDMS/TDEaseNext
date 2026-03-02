# TDEase Auto-generated Snakefile
# Generated from VueFlow workflow (V3 - Best Practices)

configfile: "config.yaml"

workdir: config.get("workdir", "results")

# Rule all - must be at the top
rule all:
    input:
        expand("{sample}_ms2.toppic_raw_prsm", sample=config["samples"])

# Rules
rule fasta_loader_1:
    input:
        "/home/ray/TDEase-Backend/UniProt_sorghum_focus1.fasta"
    output:
        "UniProt_sorghum_focus1.fasta"
    params:
        **config["nodes"]["fasta_loader_1"]["params"]
    log: "logs/fasta_loader_1.log"
    shell:
        """
                # FASTA_LOADER command with proper parameter handling
        cd .. && python3 src/nodes/fasta_loader.py \\
            --fasta /home/ray/TDEase-Backend/UniProt_sorghum_focus1.fasta \
            --output results
        """

rule data_loader_1:
    input:
        "/home/ray/TDEase-Backend/data/Sorghum-Histone0810162L20.mzML"
    output:
        "Sorghum-Histone0810162L20.mzML"
    params:
        **config["nodes"]["data_loader_1"]["params"]
    log: "logs/data_loader_1.log"
    shell:
        """
                # DATA_LOADER command with proper parameter handling
        cd .. && python3 src/nodes/data_loader.py \\
            --input /home/ray/TDEase-Backend/data/Sorghum-Histone0810162L20.mzML \
            --output results
        """

rule topfd_1:
    input:
        "{sample}.mzML"
    output:
        "{sample}_ms2.msalign"
    params:
        **config["nodes"]["topfd_1"]["params"]
    threads: 12
    log: "logs/topfd_1_{sample}.log"
    shell:
        """
                # TOPFD command with proper parameter handling
        topfd \
            -a {params.activation} \
            -c {params.max_charge} \
            -m {params.max_mass} \
            -e {params.mz_error} \
            -r {params.ms_one_sn_ratio} \
            -s {params.ms_two_sn_ratio} \
            -w {params.precursor_window} \
            -t {params.ecscore_cutoff} \
            -b {params.min_scan_number} \
            -u {params.thread_number} \
            -v {params.env_cnn_cutoff} \
            -l {params.split_intensity_ratio} \
            {input}
        """

rule toppic_1:
    input:
        fasta_file="UniProt_sorghum_focus1.fasta",
        input_files="{sample}_ms2.msalign"
    output:
        "{sample}_ms2.toppic_raw_prsm"
    params:
        fasta_file={input.fasta_file},
        **config["nodes"]["toppic_1"]["params"]
    threads: 12
    log: "logs/toppic_1_{sample}.log"
    shell:
        """
                # TOPPIC command with proper parameter handling
        toppic \
            -a {params.activation} \
            -n {params.n_terminal_form} \
            -R {params.proteoform_type} \
            -s {params.num_shift} \
            -m {params.min_shift} \
            -M {params.max_shift} \
            -S {params.variable_ptm_num} \
            -e {params.mass_error_tolerance} \
            -p {params.proteoform_error_tolerance} \
            -t {params.spectrum_cutoff_type} \
            -v {params.spectrum_cutoff_value} \
            -T {params.proteoform_cutoff_type} \
            -V {params.proteoform_cutoff_value} \
            -H {params.miscore_threshold} \
            -u {params.thread_number} \
            -r {params.num_combined_spectra} \
            {input.fasta_file} \
            {input.input_files}
        """
