// Copyright (c) 2017 Cloudera, Inc. All rights reserved.
package com.cloudera.navopt;

import com.cloudera.csd.tools.JsonUtil;
import com.cloudera.dbus.consumer.CheckpointException;
import com.cloudera.dbus.consumer.DbusCheckpointer;
import com.cloudera.dbus.DbusHeader;
import com.cloudera.dbus.DbusPayload;
import com.cloudera.dbus.DbusRecord;
import com.cloudera.dbus.consumer.DbusRecordProcessor;
import com.cloudera.dbus.consumer.DbusShutdownReason;
import com.cloudera.navigator.ipc.AvroHiveAuditEvent;
import com.fasterxml.jackson.core.type.TypeReference;
import com.google.protobuf.ByteString;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;

import java.io.IOException;
import java.io.InputStream;
import java.io.File;
import java.io.PrintWriter;
import java.nio.charset.Charset;
import java.nio.charset.CharsetDecoder;
import java.util.List;
import java.util.ArrayList;
import java.util.Map;
import java.util.HashMap;
import java.util.zip.GZIPInputStream;
import java.util.UUID;
import java.util.concurrent.TimeoutException;
import java.lang.InterruptedException;

import javax.xml.bind.DatatypeConverter;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

import org.json.simple.JSONObject;
import javax.json.Json;
import javax.json.JsonArray;
import javax.json.JsonArrayBuilder;
import javax.json.JsonObject;
import javax.json.JsonObjectBuilder;
/**
 * Logs all records and events.
 */
public class NavOptDbusRecordProcessor implements DbusRecordProcessor {

  private static final Log LOG = LogFactory.getLog(NavOptDbusRecordProcessor.class);

  private static final CharsetDecoder decoder = Charset.forName("UTF-8")
      .newDecoder();

  // Backoff and retry settings
  private static final long BACKOFF_TIME_IN_MILLIS = 3000L;
  private static final int NUM_RETRIES = 1;

  // Checkpoint about once a minute
  private static final long CHECKPOINT_INTERVAL_MILLIS = 60000L;

  private String shardId;
  private long nextCheckpointTimeInMillis;
  HashMap<String, Integer> queryid_cache = new HashMap<String, Integer>();

  /**
   * {@inheritDoc}
   */
  @Override
  public void initialize(String shardId) {
    LOG.info("Initializing record processor for shard: " + shardId);
    this.shardId = shardId;
  }

  /**
   * {@inheritDoc}
   */
  @Override
  public void processRecords(List<DbusRecord> records,
      DbusCheckpointer checkpointer) {
    LOG.info("Processing " + records.size() + " records from " + shardId);

    // Process records and perform all exception handling.
    processRecordsWithRetries(records);

    // Checkpoint once every checkpoint interval.
    if (System.currentTimeMillis() > nextCheckpointTimeInMillis) {
      checkpoint(checkpointer);
      nextCheckpointTimeInMillis = System.currentTimeMillis()
          + CHECKPOINT_INTERVAL_MILLIS;
    }
  }

  /**
   * Process records performing retries as needed. Skip "poison pill" records.
   *
   * @param records Data records to be processed.
   */
  private void processRecordsWithRetries(List<DbusRecord> records) {
    File file = new File("telemetry_data.csv");
    try {
        PrintWriter writer = new PrintWriter(file);
        writer.println("SQL_ID,ELAPSED_TIME,SQL_FULLTEXT,USER");
        for (DbusRecord record : records) {
            boolean processedSuccessfully = false;
            for (int i = 0; i < NUM_RETRIES; i++) {
                try {
                  processSingleRecord(record, writer);
                } catch (Throwable t) {
                 LOG.warn("Caught throwable while processing record " + record, t);
                }

               // backoff if we encounter an exception.
               try {
                 Thread.sleep(BACKOFF_TIME_IN_MILLIS);
               } catch (InterruptedException e) {
                 LOG.debug("Interrupted sleep", e);
              }
           }
        }
        writer.close();
    } catch (IOException e) {
        LOG.error("File not found", e);
        return;
    }
  }

  protected String getHeader(DbusRecord record, String name) {
    for (DbusHeader header : record.getHeaders()) {
      if (header.getName().equals(name)) {
        return header.getValue();
      }
    }
    return null;
  }

  /**
   * Process a single record.
   *
   * @param record The record to be processed.
   */
  private void processSingleRecord(DbusRecord record, PrintWriter writer) {
    LOG.info(
        "Processing key=" + record.getPartitionKey() + ", id="
            + record.getId());
    LOG.info("RecordId : " + record.getId());
    LOG.info("Headers : " + record.getHeaders());
    String clusterId = getHeader(record, "cluster-id");
    ByteString inlinedPayload = record.getInlinedPayload();
    if (inlinedPayload.isEmpty()) {
      try (DbusPayload payload = record.getOversizedPayload()) {
        try (InputStream is = payload.getContent()) {
            processPayload(record.getId(), record.getAccountId(), clusterId, is, writer);
        } catch (IOException e) {
          LOG.error("Error accessing oversized payload", e);
        }
      } catch (RuntimeException e) {
        LOG.error("Error accessing oversized payload", e);
      } catch (Exception e) {
        LOG.error("Error accessing oversized payload", e);
      }
    } else {
      try {
        String payloadStr = decoder.decode(record.getInlinedPayload().asReadOnlyByteBuffer()).toString();
        LOG.info("Inlined payload : " + payloadStr);
      } catch (Exception e) {
        LOG.info("Failed to decode payload as UTF-8 string");
      }
    }
  }

  private void processPayload(String recordId, String accountId, String clusterId,
        InputStream payload, PrintWriter writer) throws IOException {
      try (InputStream is = new GZIPInputStream(payload)) {
        List<AvroHiveAuditEvent> audits = JsonUtil.valueFromStream(
            new TypeReference<List<AvroHiveAuditEvent>>() {}, is);
        for (AvroHiveAuditEvent audit : audits) {
          //check if we have seen this query before
          if (!queryid_cache.containsKey(audit.getQueryId())) {
              queryid_cache.put(audit.getQueryId(), 1);
          } else {
              continue;
          }

          String queryData = '"' + audit.getQueryId() + '"' + "," + '"' + audit.getEventTime() + '"' + "," + '"' + audit.getOperationText() + '"' + "," + '"' + audit.getUsername() + '"';
          String tenant = "";
          writer.println(queryData);
          LOG.info("===> Got Query Data:" + queryData);

          //get tenant id from clusterId
          JSONObject tenantObj = new JSONObject();
          tenantObj.put("clusterId", clusterId);
          tenantObj.put("opcode", "GetTenant");
          tenantObj.put("userId", "1234");
          tenantObj.put("accountId", "whatever");
          try {
            rabbitClient rabbitObj = new rabbitClient("apiservicequeue");
            String response = rabbitObj.apiCall(tenantObj.toJSONString());
            rabbitObj.close();
            LOG.info("===> Got Response:" + response);
            Map<String, String> retMap = new Gson().fromJson(response,
                                                             new TypeToken<HashMap<String, String>>() {}.getType());
            if (retMap.containsKey("tenant")) {
                tenant = retMap.get("tenant");
                LOG.info("===> Got Tenant:" + tenant);
            }
          } catch (IOException | TimeoutException | InterruptedException e) {
            LOG.error("Exception while sending data over rabbitmq", e);
          }

          //build json object to send compiler queue...
          JSONObject obj = new JSONObject();
          obj.put("source_platform", "hive");
          obj.put("tenant", tenant);

          JsonArray list = Json.createArrayBuilder()
              .add(Json.createObjectBuilder()
                   .add("query", audit.getOperationText())
                   .add("program_type", "SQL")
                   .add("data", Json.createObjectBuilder()
                                .add("ELAPSED_TIME", audit.getEventTime())
                                .add("custom_id", audit.getQueryId())
                                .add("user", audit.getUsername()))
                   .add("countArray", Json.createArrayBuilder())
                   .add("tagArray", Json.createArrayBuilder()
                                    .add("user"))
                  )
              .build();
          obj.put("job_instances", list);
          obj.put("isTeleMetry", true);

          try {
            rabbitClient rabbitObj = new rabbitClient("compilerqueue");
            rabbitObj.call(obj.toJSONString());
            rabbitObj.close();
          } catch (IOException | TimeoutException | InterruptedException e) {
            LOG.error("Exception while sending data over rabbitmq", e);
          }
          LOG.info("Consumed HiveAudit from DataBus: " + " UserName: " + audit.getUsername() + " QueryId: "+ audit.getQueryId() + " Time: " + audit.getEventTime() + " Query:"  + audit.getOperationText());
        }
      }
  }

  /**
   * {@inheritDoc}
   */
  @Override
  public void shutdown(DbusShutdownReason reason, DbusCheckpointer checkpointer) {
    LOG.info("Shutting down record processor for shard: " + shardId);
    // Important to checkpoint after reaching end of shard, so we can start
    // processing data from child shards.
    if (reason == DbusShutdownReason.TERMINATE) {
      checkpoint(checkpointer);
    }
  }

  /**
   * Checkpoint with retries.
   *
   * @param checkpointer
   */
  private void checkpoint(DbusCheckpointer checkpointer) {
    LOG.info("Checkpointing shard " + shardId);
    for (int i = 0; i < NUM_RETRIES; i++) {
      try {
        checkpointer.checkpoint();
        break;
      } catch (CheckpointException e) {
        LOG.info(
            "Caught checkpoint exception, retryable = " + e.isRetryable(),
            e);
        if (e.isRetryable()) {
          // Backoff and retry checkpoint upon transient failures
          if (i >= (NUM_RETRIES - 1)) {
            LOG.error("Checkpoint failed after " + (i + 1) + "attempts.", e);
            break;
          } else {
            LOG.info(
                "Transient issue when checkpointing - attempt " + (i + 1) + "/"
                    + NUM_RETRIES,
                e);
          }
        } else {
          break;
        }
      }
      try {
        Thread.sleep(BACKOFF_TIME_IN_MILLIS);
      } catch (InterruptedException e) {
        LOG.debug("Interrupted sleep", e);
      }
    }
  }
}
