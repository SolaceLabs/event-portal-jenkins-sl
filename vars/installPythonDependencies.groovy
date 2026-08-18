import com.solace.ep.jenkins.Python

def call(){
    return new Python(this).installDependencies()
}