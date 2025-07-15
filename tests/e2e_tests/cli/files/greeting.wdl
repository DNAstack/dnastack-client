version 1.0
task say_hello {
    input {
        String name
    }
    command {
        echo "Hello ~{name}"
    }
    output {
        String log = read_string(stdout())
    }
    runtime {
        docker: "ubuntu:xenial"
    }
}
