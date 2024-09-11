import React, { useCallback } from "react";
import { Modal, Button, Form, Icon, List, Label } from "semantic-ui-react";
import { i18next } from "@translations/oarepo_communities";
import {
  useConfirmationModal,
  ArrayFieldItem,
  OARepoDepositSerializer,
  requiredMessage,
  returnGroupError,
  unique,
} from "@js/oarepo_ui";
import {
  ArrayField,
  TextAreaField,
  RichInputField,
  http,
  ErrorLabel,
  FieldLabel,
} from "react-invenio-forms";
import { Formik, getIn } from "formik";
import PropTypes from "prop-types";
import * as Yup from "yup";
import _debounce from "lodash/debounce";

const FormikStateLogger = ({ values }) => (
  <pre>{JSON.stringify(values, null, 2)}</pre>
);

const memberInvitationsSchema = Yup.object().shape({
  members: Yup.array()
    .of(
      Yup.object().shape({
        email: Yup.string()
          .email("Invalid email format")
          .required(requiredMessage)
          .label(i18next.t("Email")),
        firstName: Yup.string().label(i18next.t("First name")),
        lastName: Yup.string().label(i18next.t("Last name")),
      })
    )
    .required(requiredMessage)
    .label(i18next.t("Members"))
    .test("unique-emails", returnGroupError, (value, context) =>
      unique(value, context, "email", i18next.t("Emails must be unique"))
    ),
  message: Yup.string().label(i18next.t("Message")),
  membersEmails: Yup.string()
    .required(requiredMessage)
    .label(i18next.t("Members")),

  // role: Yup.string().required(requiredMessage).label(i18next.t("Role")),
});
const re = new RegExp(/[\n,]/, "g");

export const findAndValidateEmails = (value) => {
  const validEmails = [];
  const invalidEmails = [];
  const emailSchema = Yup.string().email();
  if (!value) {
    return { validEmails, invalidEmails };
  }

  const emailsArray = value.split(re).map((e) => e.trim());
  for (const email of emailsArray) {
    if (!email) {
      continue;
    }
    let processedEmail = email;

    if (email.includes("<") && email.includes(">")) {
      processedEmail = email
        .substring(email.indexOf("<") + 1, email.indexOf(">"))
        .trim();
    }
    if (emailSchema.isValidSync(processedEmail)) {
      validEmails.push(processedEmail);
    } else {
      invalidEmails.push(email);
    }
  }

  return { validEmails, invalidEmails };
};

export const CommunityInvitation = ({ rolesCanInvite, community }) => {
  const { isOpen, close, open } = useConfirmationModal();

  const onSubmit = async (values, formikBag) => {
    const serializer = new OARepoDepositSerializer(["membersEmail"], []);
    console.log(values);
    const serializedValues = serializer.serialize(values);
    serializedValues.members = serializedValues.members.map((m) => ({
      type: "email",
      id: m.email,
    }));
    console.log(serializedValues);

    await http.post(community.links.invitations, serializedValues);
  };

  const debouncedValidateEmails = useCallback(
    _debounce((value, setFieldValue) => {
      const emails = findAndValidateEmails(value);
      setFieldValue("emails", emails);
    }, 1000),
    []
  );

  const handleChange = (value, setFieldValue) => {
    setFieldValue("membersEmails", value);
    debouncedValidateEmails(value, setFieldValue);
  };
  const usersCanInvite = rolesCanInvite.user;
  return (
    <Formik
      onSubmit={onSubmit}
      initialValues={{
        membersEmails: "",
        members: [],
        message: "",
        role: "member",
        emails: { validEmails: [], invalidEmails: [] },
      }}
      validateOnChange={false}
      validateOnBlur={true}
      enableReinitialize={true}
      validationSchema={memberInvitationsSchema}
    >
      {({
        values,
        setFieldValue,
        setFieldTouched,
        handleSubmit,
        resetForm,
      }) => (
        <Modal
          className="form-modal"
          closeIcon
          open={isOpen}
          onClose={close}
          onOpen={open}
          trigger={
            <Button
              className="fluid-responsive"
              content={i18next.t("Invite...")}
              positive
              fluid
              compact
              icon="user plus"
              labelPosition="left"
              aria-expanded={isOpen}
              aria-haspopup="dialog"
            />
          }
        >
          <Modal.Header>
            {i18next.t("Invite users to the {{communityTitle}} community", {
              communityTitle: community.metadata.title,
            })}
          </Modal.Header>
          <Modal.Content>
            <Form>
              <Form.Field>
                <TextAreaField
                  className="mb-0"
                  fieldPath="membersEmails"
                  optimized
                  required
                  label={<FieldLabel label={i18next.t("Members")} />}
                  onChange={(e, { value }) =>
                    handleChange(value, setFieldValue)
                  }
                />
                {values.emails.invalidEmails.length > 0 && (
                  <Label
                    pointing
                    prompt
                    content={`${i18next.t(
                      "Invalid emails"
                    )}: ${values.emails.invalidEmails.join(",")}`}
                  />
                )}
              </Form.Field>

              <label className="helptext">
                {i18next.t(
                  "Emails shall be provided on separate lines. Acceptable formats are johndoe@user.com or John Doe <johndoe@user.com>."
                )}
              </label>
              <Form.Field required className="rel-mt-1">
                <FieldLabel label={i18next.t("Role")} />
                <List selection>
                  {usersCanInvite.map((u) => (
                    <List.Item
                      key={u.name}
                      onClick={() => {
                        if (values.role === u.name) return;
                        setFieldValue("role", u.name);
                      }}
                      active={values.role === u.name}
                    >
                      <List.Content>
                        <List.Header>{u.title}</List.Header>
                        <List.Description>{u.description}</List.Description>
                      </List.Content>
                    </List.Item>
                  ))}
                </List>
                <ErrorLabel fieldPath="role" />
              </Form.Field>
              <RichInputField
                className="rel-mt-1"
                label={<FieldLabel label={i18next.t("Message")} />}
                fieldPath="message"
                optimized
                inputValue={() => getIn(values, "message", "")}
                initialValue=""
              />
              {/* <FormikStateLogger values={values} /> */}
            </Form>
          </Modal.Content>
          <Modal.Actions>
            <Button
              onClick={() => {
                close();
                resetForm();
              }}
              floated="left"
            >
              <Icon name="remove" /> {i18next.t("Cancel")}
            </Button>
            <Button
              primary
              onClick={handleSubmit}
              disabled={values.members.length === 0}
            >
              <Icon name="checkmark" /> {i18next.t("Invite")}
            </Button>
          </Modal.Actions>
        </Modal>
      )}
    </Formik>
  );
};

CommunityInvitation.propTypes = {
  rolesCanInvite: PropTypes.object.isRequired,
  community: PropTypes.object.isRequired,
};
