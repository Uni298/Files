javac -cp spigot-api-1.20.1.jar -d out *.java
jar cf Main.jar -C out . -C plugin.yml config.yml *.class
echo Done!
