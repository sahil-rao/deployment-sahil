// Copyright (c) 2017 Cloudera, Inc. All rights reserved.
package com.cloudera.navopt;

import com.rabbitmq.client.ConnectionFactory;
import com.rabbitmq.client.Connection;
import com.rabbitmq.client.Channel;
import com.rabbitmq.client.DefaultConsumer;
import com.rabbitmq.client.AMQP;
import com.rabbitmq.client.Envelope;

import java.io.IOException;
import java.util.UUID;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.TimeoutException;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Map;
import java.util.List;

import ca.szc.configparser.Ini;
import ca.szc.configparser.exceptions.IniParserException;
import ca.szc.configparser.exceptions.NoSectionError;
import ca.szc.configparser.exceptions.ParsingError;
import ca.szc.configparser.exceptions.NoOptionError;
import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

public class rabbitClient {

  private Connection connection;
  private Channel channel;
  private String requestQueueName;
  private String replyQueueName;
  private static final Log LOG = LogFactory.getLog(rabbitClient.class);

  public rabbitClient(String queueName) throws IOException, TimeoutException {
    requestQueueName = queueName;
    ConnectionFactory factory = new ConnectionFactory();

    // Read from a file
    Path input = Paths.get("/var/Baaz/hosts.cfg");
    Ini ini = new Ini().read(input);
    Map<String, Map<String, String>> sections = ini.getSections();
    try {
        String rabbit_hosts = ini.getValue("RabbitMQ", "server");
        String[] hosts  = rabbit_hosts.split(",");
        String username = ini.getValue("RabbitMQ", "username");
        String password = ini.getValue("RabbitMQ", "password");
        factory.setHost(hosts[0]);
        factory.setUsername(username);
        factory.setPassword(password);
        factory.setVirtualHost("xplain");
        LOG.info("Username:"+ username + " password:" + password + " host:"+ hosts[0]);
        connection = factory.newConnection();
        channel = connection.createChannel();

        replyQueueName = channel.queueDeclare().getQueue();
    } catch (IniParserException | NoSectionError | NoOptionError e) {
        LOG.info("Non-expected ParsingErrors were generated: " + e);
    }
  }

  public void call(String message) throws IOException, InterruptedException {
    String corrId = UUID.randomUUID().toString();

    AMQP.BasicProperties props = new AMQP.BasicProperties
            .Builder()
            .correlationId(corrId)
            .replyTo(replyQueueName)
            .build();

    channel.basicPublish("", requestQueueName, props, message.getBytes("UTF-8"));

    return;
  }

  public String apiCall(String message) throws IOException, InterruptedException {
    String corrId = UUID.randomUUID().toString();

    AMQP.BasicProperties props = new AMQP.BasicProperties
            .Builder()
            .correlationId(corrId)
            .replyTo(replyQueueName)
            .build();

    channel.basicPublish("", requestQueueName, props, message.getBytes("UTF-8"));

    final BlockingQueue<String> response = new ArrayBlockingQueue<String>(1);

    channel.basicConsume(replyQueueName, true, new DefaultConsumer(channel) {
      @Override
      public void handleDelivery(String consumerTag, Envelope envelope, AMQP.BasicProperties properties, byte[] body) throws IOException {
        if (properties.getCorrelationId().equals(corrId)) {
          response.offer(new String(body, "UTF-8"));
        }
      }
    });

    return response.take();
  }

  public void close() throws IOException {
    connection.close();
  }
}
