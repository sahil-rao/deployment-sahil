package com.cloudera.navopt;

import com.amazonaws.auth.profile.ProfileCredentialsProvider;
import com.cloudera.dbus.consumer.DbusClient;
import com.cloudera.dbus.consumer.DbusStreamPosition;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.io.IOException;
import java.util.concurrent.TimeoutException;
import java.lang.InterruptedException;

public class Main {

  private static final Logger LOG = LoggerFactory.getLogger(Main.class);

  public static void main(String[] args) throws Exception {

    if (args.length < 1) {
      System.out.println("Stream name must be specified.");
      return;
    }
    String streamName = args[0];

    /*
     * The ProfileCredentialsProvider will return your [default] credential
     * profile by reading from the credentials file located at
     * (~/.aws/credentials).
     */
    DbusClient dbusClient = DbusClient.builder()
        .setStreamName(streamName)
        .setAppName("NavOpt")
        .setCredentialsProvider(new ProfileCredentialsProvider())
        .setProcessorFactory(new NavOptDbusRecordProcessorFactory())
        .setPosition(DbusStreamPosition.LATEST)
        .build();

    System.out
        .printf("Running sample app to process stream %s...%n", streamName);

    int exitCode = 0;
    try {
      dbusClient.run();
    } catch (Throwable t) {
      System.err.println("Caught throwable while processing data.");
      t.printStackTrace();
      exitCode = 1;
    }
    System.exit(exitCode);
  }
}