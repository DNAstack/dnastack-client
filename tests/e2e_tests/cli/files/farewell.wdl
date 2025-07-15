version 1.0
task say_goodbye {
    input {
        String name
    }
    command {
        echo "Goodbye ~{name}"
    }
    output {
        String log = read_string(stdout())
    }
    runtime {
        docker: "ubuntu:xenial"
    }
}
