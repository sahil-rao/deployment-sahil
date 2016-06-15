# (c) Copyright 2015 Cloudera, Inc. All rights reserved.

from flightpath.Provenance import getMongoServer
import sys

t_and_c_text = '<p><b>CLOUDERA BETA AGREEMENT FOR ONLINE SERVICES</b><span> - Updated 5/26/2016</span></p><p><span>&nbsp;THIS BETA AGREEMENT FOR ONLINE SERVICES (THIS &quot;AGREEMENT&quot;) APPLIES TO YOUR USE OF THE ONLINE SERVICES (AS DEFINED BELOW) PROVIDED BY CLOUDERA, INC. OR ITS SUBSIDIARIES (&quot;CLOUDERA&quot;).</span></p><p><span>PLEASE READ THE TERMS AND CONDITIONS OF THIS AGREEMENT CAREFULLY.</span></p><p><span>BY ACCESSING AND USING THE ONLINE SERVICES, YOU ACKNOWLEDGE AND AGREE THAT: (I)&nbsp;YOU HAVE READ ALL OF THE TERMS AND CONDITIONS OF THIS AGREEMENT; (II)&nbsp;YOU UNDERSTAND ALL OF THE TERMS AND CONDITIONS OF THIS AGREEMENT; AND (III)&nbsp;YOU AGREE TO BE BOUND BY ALL OF THE TERMS AND CONDITIONS OF THIS AGREEMENT. &nbsp;IF YOU DO NOT AGREE TO ALL OF THE TERMS OR CONDITIONS OF THIS AGREEMENT, YOU MAY NOT USE ANY PORTION OF THE ONLINE SERVICES.</span></p><p><span>IF YOU ARE ENTERING INTO THIS AGREEMENT ON BEHALF OF A COMPANY (OR OTHER ENTITY), YOU REPRESENT THAT YOU ARE THE EMPLOYEE OR AGENT OF SUCH COMPANY (OR OTHER ENTITY) AND YOU HAVE THE AUTHORITY TO ENTER INTO THIS AGREEMENT ON BEHALF OF SUCH COMPANY (OR OTHER ENTITY).</span></p><p><span>THE &quot;EFFECTIVE DATE&quot; OF THIS AGREEMENT IS THE EARLIER OF: (I) THE DATE YOU ACCEPTED THESE TERMS ON-LINE OR (II)&nbsp;THE DATE YOU OR ANOTHER REPRESENTATIVE OF YOUR COMPANY FIRST ACCESSED THE ONLINE SERVICES.</span></p><p><span>FOR THE PURPOSE OF THIS AGREEMENT, YOU AND, IF APPLICABLE, SUCH COMPANY (OR OTHER ENTITY) CONSTITUTES &quot;CUSTOMER&quot;.</span></p><p><span>THIS AGREEMENT CONSTITUTES AN ENFORCEABLE AGREEMENT BY AND BETWEEN YOU (OR THE COMPANY YOU REPRESENT, AS APPLICABLE) AND CLOUDERA.</span></p><p><b>License; Access</b><span>.&nbsp;During the period between the Effective Date and the date on which the Online Services becomes generally available (&quot;Beta Period&quot;), or, if the software does not become publicly available, the date upon which Cloudera notifies Customer that the Beta Period has expired, Cloudera grants to Customer a nonexclusive, nontransferable, nonsublicensable, revocable and limited license to access and use, in accordance with the Documentation, the beta version of the Online Services as provided by Cloudera on a website solely for Customer&#39;s internal evaluation purposes. &nbsp;&ldquo;Online Services&rdquo; means the web services offered by Cloudera at </span><span>https://optimizer.cloudera.com</span><span>&nbsp;or other site branded by Cloudera from which the services may be accessed. &nbsp;&ldquo;Documentation&rdquo; means the applicable documentation as provided by Cloudera on its web site.</span></p><p><b>License Restrictions</b><span>. Except as expressly authorized by this Agreement, Customer may not: (i)&nbsp;modify, translate or create derivative works of the Online Services, including any software included therein; (ii)&nbsp;publicly perform, display, discuss or otherwise distribute any portion of the Software; (iii)&nbsp;sell, assign, sublicense, rent, lease, loan, provide, distribute or otherwise transfer all or any portion of the Online Service; (iv)&nbsp;allow the transfer, transmission, export, or re-export of the Online Service, or any portion thereof, in violation of any export control laws or regulations administered by the U.S. Commerce Department, OFAC, or any other government agency; (v)&nbsp;access or use the Online Service in order to build a competitive product or service or copy any features, functions or graphics of the Online Service; or (vi)&nbsp;cause or permit any other party to do any of the foregoing. In addition, Customer will not remove, alter or obscure any proprietary notices in the Online Service, including copyright notices, or permit any other party to do so.</span></p><p><b>Customer Obligations</b><span>. Customer agrees to: (i)&nbsp;provide Cloudera with representative data and queries via the Online Service; (ii)&nbsp;work with Cloudera to evaluate the Online Service; (iii)&nbsp;provide Cloudera with detailed feedback regarding the Online Service including, but not limited to, participating in periodic meetings with Cloudera to discuss the Online Service&#39;s functionality; and (iv)&nbsp;comply with any policies that Cloudera may adopt regarding privacy, acceptable use, and/or data security, which policies shall be made available to Customer on Cloudera&rsquo;s web site. </span></p><p><b>Marketing and Publicity</b><span>. &nbsp;At Customer&rsquo;s discretion, Customer may participate in Online Service marketing support activities including, but not limited to collaborating with Cloudera in the preparation of any public announcements, including case studies, that Cloudera issues regarding the Online Service, presenting the Online Service alongside Cloudera at industry events and offering evaluations and feedback about the Online Service that may be leveraged for the production of a written and/or video case study (collectively, &quot;Online Service Evaluations&rdquo;). &nbsp;With Customer&rsquo;s consent, Cloudera may display Customer logo on Cloudera&rsquo;s customer lists or marketing materials.</span></p><p><b>Ownership</b><span>. As between the parties and subject to the grants under this Agreement, Cloudera owns all right, title and interest in and to the Feedback (as defined below), the Online Service Evaluations and the Online Service and any and all related patents, copyrights, moral rights, trademarks, trade secrets and any other form of intellectual property rights recognized in any jurisdiction (including applications and registrations for any of the foregoing) embodied in the foregoing.</span></p><p><b>Customer Data</b><span>. &nbsp;As between Customer and Cloudera, Customer or its licensors owns all right, title, and interest in and to the Customer Data (as defined below). &nbsp;Customer consents to Cloudera&rsquo;s use of the Customer Data to provide the Online Services. &nbsp;Cloudera may only use Customer Data for Cloudera&rsquo;s &nbsp;internal purposes, including testing, research, training, diagnostics and feature improvement, if it receives Customer&rsquo;s prior written consent. &nbsp;Cloudera may disclose Customer Data as necessary to provide the Online Services to Customer or to comply with any request of a governmental or regulatory body (including subpoenas or court orders). &nbsp;Cloudera has no obligation to account or pay for such use or disclosure. &nbsp;Customer represents and warrants to Cloudera that: (a) Customer or its licensors own all right, title, and interest in and to all Customer Data; (b) Customer has all rights in all Customer Data necessary to grant the rights contemplated by this Agreement; and (c) none of the Customer Data nor Customer&rsquo;s or Cloudera&rsquo;s use of the Customer Data or the Online Services will violate applicable law or Cloudera policies as posted to Cloudera&rsquo;s website. &ldquo;Customer Data&rdquo; means Data that Customer (or any end user on behalf of Customer) (x) runs on the Cloudera Online Services, (y) causes to interface with the Online Services, or (z) uploads to the Online Services under Customer&rsquo;s account or otherwise transfer, process, use or store in connection with Customer&rsquo;s account. &nbsp;&ldquo;Data&rdquo; means any software (including machine images), data, text, audio, video, images or other content.</span></p><p><b>Acceptable Use</b><span>. &nbsp;Customer may not use, or encourage, promote, facilitate or instruct others to use, the Online Services for any illegal, harmful or offensive use, or to transmit, store, display, distribute or otherwise make available content that is illegal, harmful, or offensive. &nbsp;Customer may not use the Online Services to violate the security or integrity of any network, computer or communications system, software application, or network or computing device. &nbsp;Customer may not make network connections to any users, hosts, or networks unless Customer has permission to communicate with them.</span></p><p><b>Nondisclosure and Publicity</b><span>. &quot;Confidential Information&quot; means all information disclosed (whether in oral, written, or other tangible or intangible form) by Cloudera to Customer concerning or related to this Agreement or Cloudera (whether before, on or after the Effective Date) which Customer knows or should know, given the facts and circumstances surrounding the disclosure of the information by Cloudera, is confidential information of Cloudera. Confidential Information includes, but is not limited to, the components of the business plans, the Online Services, inventions, design plans, financial plans, computer programs, know-how, customer information, strategies, benchmark and other testing results, and other similar information. Customer will, during the term of this Agreement and thereafter, maintain in confidence the Confidential Information and will not use such Confidential Information except as expressly permitted herein. Customer will use the same degree of care in protecting the Confidential Information as Customer uses to protect its own confidential information from unauthorized use or disclosure, but in no event less than reasonable care. Confidential Information will be used by Customer solely for the purpose of carrying out Customer&#39;s obligations under this Agreement. Confidential Information will not include information that: (i)&nbsp;is in or enters the public domain without breach of this Agreement through no fault of Customer; (ii)&nbsp;Customer can reasonably demonstrate was in its possession prior to first receiving it from Cloudera; (iii)&nbsp;Customer can demonstrate was developed by Customer independently and without use of or reference to the Confidential Information; or (iv)&nbsp;Customer receives from a third party without restriction on disclosure and without breach of a nondisclosure obligation. Notwithstanding any terms to the contrary in this Agreement, any suggestions, comments or other feedback, including the results of any benchmark or other testing, provided by Customer to Cloudera with respect to the Online Services (collectively, &quot;Feedback&quot;) will constitute Confidential Information. Further, Cloudera will be free to use, disclose, reproduce, license and otherwise distribute, and exploit the Feedback provided to it as it sees fit, entirely without obligation or restriction of any kind on account of Intellectual Property Rights or otherwise. Customer consents to Cloudera&#39;s use of Customer&#39;s name and logo on Cloudera&#39;s website and publicly-available materials, identifying Customer as a customer of Cloudera and describing Customer&#39;s use of the Software.</span></p><p><b>Indemnity</b><span>. &nbsp;Customer will defend, indemnify, and hold harmless Cloudera, its affiliates and licensors, and each of their respective employees, officers, directors, and representatives from and against any damages, settlements, liabilities, costs and expenses (including, but not limited to, reasonable attorney fees) arising out of or relating to any third party claim concerning: (i) Customer&rsquo;s use of the Online Services; (b) breach of this Agreement or violation of applicable law by Customer; or (c) Customer Data (or the combination of Customer Data with other applications, content or processes), including any claim involving alleged infringement or misappropriation of third-party rights by Customer Data or by the use, development, design, production, advertising or marketing of Customer Data. If Cloudera or its affiliates are obligated to respond to a third party subpoena or other compulsory legal order or process described above, Customer will also reimburse Cloudera for reasonable attorneys&rsquo; fees. &nbsp;Cloudera will promptly notify Customer of any claim subject to this section, but Cloudera&rsquo;s failure to promptly notify Customer will only affect Customer&rsquo;s obligations under this section to the extent that such failure prejudices Customer&rsquo;s ability to defend the claim. &nbsp;Cloudera may also assume control of the defense and settlement of the claim at any time.</span></p><p><b>Disclaimer</b><span>. THE ONLINE SERVICES ARE PROVIDED ON AN &quot;AS IS&quot; OR &quot;AS AVAILABLE&quot; BASIS WITHOUT ANY REPRESENTATIONS, WARRANTIES, COVENANTS OR CONDITIONS OF ANY KIND. CLOUDERA AND ITS SUPPLIERS DO NOT WARRANT THAT THE ONLINE SERVICES WILL BE FREE FROM BUGS, ERRORS, OR OMISSIONS. CLOUDERA AND ITS SUPPLIERS DISCLAIM ANY AND ALL WARRANTIES AND REPRESENTATIONS (EXPRESS OR IMPLIED, ORAL OR WRITTEN) WITH RESPECT TO THE ONLINE SERVICES WHETHER ALLEGED TO ARISE BY OPERATION OF LAW, BY REASON OF CUSTOM OR USAGE IN THE TRADE, BY COURSE OF DEALING OR OTHERWISE, INCLUDING ANY AND ALL (I)&nbsp;WARRANTIES OF MERCHANTABILITY, (II)&nbsp;WARRANTIES OF FITNESS OR SUITABILITY FOR ANY PURPOSE (WHETHER OR NOT CLOUDERA KNOWS, HAS REASON TO KNOW, HAS BEEN ADVISED, OR IS OTHERWISE AWARE OF ANY SUCH PURPOSE), AND (III)&nbsp;WARRANTIES OF NONINFRINGEMENT OR CONDITION OF TITLE. CUSTOMER ACKNOWLEDGES AND AGREES THAT CUSTOMER HAS RELIED ON NO WARRANTIES. CLOUDERA DOES NOT GUARANTEE THAT THE BETA ONLINE SERVICES WILL BE MADE GENERALLY AVAILABLE, OR THAT ANY INDIVIDUAL FEATURE IN THE BETA VERSION WILL BE MADE GENERALLY AVAILABLE. CLOUDERA MAY MAKE THE BETA ONLINE SERVICES GENERALLY AVAILABLE, OR NOT, IN ITS SOLE DISCRETION AND WITHOUT OBLIGATION TO MAKE ANY COMMUNICATION TO OF ANY KIND WITH REGARD TO SUCH AVAILABILITY.</span></p><p><b>Limitation of Liability</b><span>. IN NO EVENT WILL: (I)&nbsp;CLOUDERA BE LIABLE TO CUSTOMER OR ANY THIRD PARTY FOR ANY LOSS OF PROFITS, LOSS OF USE, LOSS OF REVENUE, LOSS OF GOODWILL, ANY INTERRUPTION OF BUSINESS, OR FOR ANY INDIRECT, SPECIAL, INCIDENTAL, EXEMPLARY, PUNITIVE OR CONSEQUENTIAL DAMAGES OF ANY KIND ARISING OUT OF OR IN CONNECTION WITH THIS AGREEMENT, THE &nbsp;ONLINE SERVICES, OR THE CUSTOMER DATA, REGARDLESS OF THE FORM OF ACTION, WHETHER IN CONTRACT, TORT, STRICT LIABILITY OR OTHERWISE, EVEN IF CLOUDERA HAS BEEN ADVISED OR IS OTHERWISE AWARE OF THE POSSIBILITY OF SUCH DAMAGES; AND (II)&nbsp;CLOUDERA&#39;S TOTAL LIABILITY ARISING OUT OF OR RELATED TO THIS AGREEMENT EXCEED THE AGGREGATE OF THE AMOUNTS PAID OR PAYABLE BY CUSTOMER TO CLOUDERA, IF ANY, UNDER THIS AGREEMENT. MULTIPLE CLAIMS WILL NOT EXPAND THIS LIMITATION.</span></p><p><b>Termination</b><span>. Unless terminated as set forth herein, the term of this Agreement will commence on the Effective Date and continue through the Beta Period. Cloudera may immediately terminate access to the Online Services and/or this Agreement in its discretion. Upon the expiration or termination of this Agreement: (i)&nbsp;all rights granted to Customer under this Agreement will immediately cease; and (ii)&nbsp;Customer will promptly provide Cloudera with all Confidential Information then in its possession or destroy all copies of such Confidential Information, at Cloudera&#39;s sole discretion and direction. Notwithstanding any terms to the contrary in this Agreement, in addition to all definitions and this sentence, the following Sections will survive any termination or expiration of this Agreement: License Restrictions; Customer Data; Customer Obligations; Ownership; Nondisclosure and Publicity; Disclaimer; Limitation of Liability, Third Party Licenses, and Miscellaneous.</span></p><p><b>Miscellaneous</b><span>. This Agreement together with any exhibits attached hereto, are the entire agreement of the parties regarding the subject matter hereof, superseding all other agreements between them, whether oral or written, regarding the subject matter hereof. This Agreement will be governed by and construed in accordance with the laws of the State of California applicable to agreements made and to be entirely performed within the State of California, without resort to its conflict of law provisions. The parties agree that any action at law or in equity arising out of or relating to this Agreement will be filed only in the state and federal courts located in San Mateo County, California. The parties hereby irrevocably and unconditionally consent and submit to the exclusive jurisdiction of such courts over any suit, action or proceeding arising out of this Agreement. Neither this Agreement nor any right or duty under this Agreement may be transferred, assigned or delegated by Customer, by operation of law or otherwise, without the prior written consent of Cloudera, and any attempted transfer, assignment or delegation without such consent will be void and without effect. Cloudera may freely transfer, assign or delegate this Agreement or its rights and duties under this Agreement. Subject to the foregoing, this Agreement will be binding upon and will inure to the benefit of the parties and their respective representatives, heirs, administrators, successors and permitted assigns. If any provision of this Agreement is invalid, illegal, or incapable of being enforced by any rule of law or public policy, all other provisions of this Agreement will nonetheless remain in full force and effect so long as the economic or legal substance of the transactions contemplated by this Agreement is not affected in any manner adverse to any party. Upon such determination that any provision is invalid, illegal, or incapable of being enforced, the parties will negotiate in good faith to modify this Agreement so as to effect the original intent of the parties as closely as possible in an acceptable manner to the end that the transactions contemplated hereby are fulfilled. Notwithstanding any terms to the contrary in this Agreement, Cloudera may choose to electronically deliver all communications with Customer, which may include email to Customer&#39;s email address indicated in Customer&#39;s communications with Cloudera. Cloudera&#39;s electronic communications to Customer may transmit or convey information about action taken on Customer&#39;s request, portions of Customer&#39;s request that may be incomplete or require additional explanation, any notices required under applicable law and any other notices. Customer agrees to do business electronically with Cloudera, and to receive electronically all current and future notices, disclosures, communications and information, and that the aforementioned provided electronically satisfies any legal requirement that such communications be in writing. An electronic notice will be deemed to have been received the day of receipt as evidenced by such email.</span></p></p>'
tenant = 'xplainIO'
client = getMongoServer(tenant)

cur_version = 2
db = client['xplainIO']
db.terms_and_conditions.update({'version': cur_version},
                               {'$set': {'text': t_and_c_text,
                                         'version': cur_version}}, upsert=True)

if len(sys.argv) > 1 and sys.argv[1]:
    db.users.update({}, {'$set': {'signed_terms': False}}, multi=True)
