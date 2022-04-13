import React, { useState } from "react";
import { Formik } from "formik";
import {
  Header,
  Form,
  Button,
  Message,
  Segment,
  Dropdown,
} from "semantic-ui-react";
import { DateInput } from "semantic-ui-calendar-react";
import moment from "moment";

import { submitNote } from "./case-file-note";
import { TextArea } from "comps/textarea";

export const EligibilityForm = ({ issue, setIssue, setNotes, onCancel }) => {
  const [isSuccess, setSuccess] = useState(false);
  return (
    <Segment>
      <Header>Log an eligibility check</Header>
      <p>
        Leave a note to record that you have performed an eligibility check for
        this case.
      </p>
      <Formik
        initialValues={{ text: "", note_type: "" }}
        validate={({ text, note_type }) => {
          const errors = {};
          if (!text) errors.text = "File note cannot be empty";
          if (!note_type) errors.note_type = "Outcome is required";
          return errors;
        }}
        onSubmit={submitNote(issue, setIssue, setNotes, setSuccess)}
      >
        {({
          values,
          errors,
          handleChange,
          handleSubmit,
          isSubmitting,
          setFieldValue,
        }) => (
          <Form
            onSubmit={handleSubmit}
            success={isSuccess}
            error={Object.keys(errors).length > 0}
          >
            <Dropdown
              fluid
              selection
              loading={isSubmitting}
              placeholder="Select an outcome"
              options={[
                {
                  key: "ELIGIBILITY_CHECK_SUCCESS",
                  value: "ELIGIBILITY_CHECK_SUCCESS",
                  text: "Cleared",
                },
                {
                  key: "ELIGIBILITY_CHECK_FAILURE",
                  value: "ELIGIBILITY_CHECK_FAILURE",
                  text: "Not cleared",
                },
              ]}
              onChange={(e, { value }) =>
                setFieldValue("note_type", value, false)
              }
            />

            <TextArea
              onChange={(e) => setFieldValue("text", e.target.value, false)}
              disabled={isSubmitting}
              placeholder="Write a note describing why the outcome was chosen."
              rows={3}
              value={values.text}
              style={{ margin: "1em 0" }}
            />

            {Object.entries(errors).map(([k, v]) => (
              <Message error key={k}>
                <div className="header">{k}</div>
                <p>{v}</p>
              </Message>
            ))}
            <Button
              loading={isSubmitting}
              disabled={isSubmitting}
              positive
              type="submit"
            >
              Create record
            </Button>
            <Button disabled={isSubmitting} onClick={onCancel}>
              Close
            </Button>
            <Message success>Eligibility check created</Message>
          </Form>
        )}
      </Formik>
    </Segment>
  );
};
