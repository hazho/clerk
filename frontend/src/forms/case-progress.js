import React, { useState } from "react";
import { Formik } from "formik";
import { Header, Form, Button, Message, Segment } from "semantic-ui-react";
import { DateInput } from "semantic-ui-calendar-react";
import moment from "moment";

import { api } from "api";

export const ProgressForm = ({ issue, setIssue, setNotes, onCancel }) => {
  return <h1>PerformanceForm</h1>;
};
