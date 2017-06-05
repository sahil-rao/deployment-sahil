// Copyright (c) 2017 Cloudera, Inc. All rights reserved.
package com.cloudera.navopt;

import com.cloudera.dbus.consumer.DbusRecordProcessor;
import com.cloudera.dbus.consumer.DbusRecordProcessorFactory;

import org.apache.commons.logging.Log;
import org.apache.commons.logging.LogFactory;

/**
 * Used to create new record processors.
 */
public class NavOptDbusRecordProcessorFactory implements DbusRecordProcessorFactory {

  private static final Log LOG = LogFactory
      .getLog(NavOptDbusRecordProcessorFactory.class);

  @Override
  public DbusRecordProcessor createProcessor() {
    LOG.info("Creating new SampleRecordProcessor");
    return new NavOptDbusRecordProcessor();
  }
}
