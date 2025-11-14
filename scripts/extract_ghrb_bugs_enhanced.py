#!/usr/bin/env python3
"""
Extract bug reports from GHRB dataset with enhanced information.
Includes actual bug descriptions from the paper and GitHub issues.
"""

import json
import os
from pathlib import Path
import subprocess
import re

# Complete GHRB bug information from the LIBRO paper
# These are all 31 bugs used in the GHRB evaluation
GHRB_BUGS = [
    {
        "project": "assertj-core",
        "issue_number": "2319",
        "pr_number": "2324",
        "title": "hasMethods does not work on default methods",
        "description": """Summary
IMO hasMethod should really follow the same contract as Class.getMethod(), but it doesn't when it comes to default methods inherited from an interface (that are not overridden with an implementation in the class being asserted).
This is because org.assertj.core.internal.Classes.getAllMethods(Class) only looks at parent classes and not any implemented interfaces.
Example
class DefaultHasMethodTest {
  interface HasDefault {
    default void method() {}
  }
  static class Impl implements HasDefault {
  }
  @Test
  void testHasMethod() throws Exception {
    assertThat(Impl.class).hasMethods("method");
  }
}
This might be related to #880.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "assertj-core",
        "issue_number": "2363",
        "pr_number": "2364",
        "title": "Extracting through field names not supported for optional in java 17",
        "description": """Summary
I'm upgrading to java 17 (from java 11), and I have some tests failing due to an incompatibility between java 17 and assertJ.
One of the breaking changes introduced by java 17 is JEP 396: Strongly Encapsulate JDK Internals by Default.
It seems that assertJ try to force access to non public value (not public) when extracting them through field name => extract the value from an optional ("object.value") and since the value is not public I got this exception:
org.assertj.core.util.introspection.IntrospectionError:
Can't find any field or property with name 'value'.
Error when introspecting properties was :
- No getter for property 'value' in java.util.Optional
Error when introspecting fields was :
- Unable to obtain the value of the field  from
	at org.assertj.core.util.introspection.PropertyOrFieldSupport.getSimpleValue(PropertyOrFieldSupport.java:88)
	at org.assertj.core.util.introspection.PropertyOrFieldSupport.getValueOf(PropertyOrFieldSupport.java:60)
	at org.assertj.core.util.introspection.PropertyOrFieldSupport.getValueOf(PropertyOrFieldSupport.java:57)
	at org.assertj.core.extractor.ByNameSingleExtractor.apply(ByNameSingleExtractor.java:29)
	at org.assertj.core.api.AbstractAssert.extracting(AbstractAssert.java:1059)
	at org.assertj.core.api.AbstractObjectAssert.extracting(AbstractObjectAssert.java:834)
	at fr.witchbird.cl.negotiation.test.functional.VersionIT.should_access(VersionIT.java:165)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:77)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:568)
	at org.junit.runners.model.FrameworkMethod$1.runReflectiveCall(FrameworkMethod.java:50)
	at org.junit.internal.runners.model.ReflectiveCallable.run(ReflectiveCallable.java:12)
	at org.junit.runners.model.FrameworkMethod.invokeExplosively(FrameworkMethod.java:47)
	at org.junit.internal.runners.statements.InvokeMethod.evaluate(InvokeMethod.java:17)
	at org.junit.runners.ParentRunner.runLeaf(ParentRunner.java:325)
	at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:78)
	at org.junit.runners.BlockJUnit4ClassRunner.runChild(BlockJUnit4ClassRunner.java:57)
	at org.junit.runners.ParentRunner$3.run(ParentRunner.java:290)
	at org.junit.runners.ParentRunner$1.schedule(ParentRunner.java:71)
	at org.junit.runners.ParentRunner.runChildren(ParentRunner.java:288)
	at org.junit.runners.ParentRunner.access$000(ParentRunner.java:58)
	at org.junit.runners.ParentRunner$2.evaluate(ParentRunner.java:268)
	at org.junit.runners.ParentRunner.run(ParentRunner.java:363)
	at org.junit.runner.JUnitCore.run(JUnitCore.java:137)
	at com.intellij.junit4.JUnit4IdeaTestRunner.startRunnerWithArgs(JUnit4IdeaTestRunner.java:69)
	at com.intellij.rt.junit.IdeaTestRunner$Repeater.startRunnerWithArgs(IdeaTestRunner.java:33)
	at com.intellij.rt.junit.JUnitStarter.prepareStreamsAndStart(JUnitStarter.java:235)
	at com.intellij.rt.junit.JUnitStarter.main(JUnitStarter.java:54)
Caused by: org.assertj.core.util.introspection.IntrospectionError: Unable to obtain the value of the field  from
	at org.assertj.core.util.introspection.FieldSupport.readSimpleField(FieldSupport.java:248)
	at org.assertj.core.util.introspection.FieldSupport.fieldValue(FieldSupport.java:202)
	at org.assertj.core.util.introspection.PropertyOrFieldSupport.getSimpleValue(PropertyOrFieldSupport.java:70)
	... 28 more
Caused by: java.lang.reflect.InaccessibleObjectException: Unable to make field private final java.lang.Object java.util.Optional.value accessible: module java.base does not "opens java.util" to unnamed module @7fbe847c
	at java.base/java.lang.reflect.AccessibleObject.checkCanSetAccessible(AccessibleObject.java:354)
	at java.base/java.lang.reflect.AccessibleObject.checkCanSetAccessible(AccessibleObject.java:297)
	at java.base/java.lang.reflect.Field.checkCanSetAccessible(Field.java:178)
	at java.base/java.lang.reflect.Field.setAccessible(Field.java:172)
	at org.assertj.core.util.introspection.FieldUtils.getField(FieldUtils.java:67)
	at org.assertj.core.util.introspection.FieldUtils.readField(FieldUtils.java:143)
	at org.assertj.core.util.introspection.FieldSupport.readSimpleField(FieldSupport.java:208)
	... 30 more
Example
       private static class Person {
		private final Optional name;
		public Person(final Optional name) {
			this.name = name;
		}
		public Optional getName() {
			return name;
		}
	}
	@Test
	public void should_access() {
		final Optional name = Optional.of("john");
		final var person = new Person(name);
		Assertions.assertThat(person)
		        .extracting("name.value")
		        .isEqualTo("john");
	}""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "assertj-core",
        "issue_number": "2444",
        "pr_number": "2445",
        "title": "isExactlyInstanceOf gives confusing error message when instance is an anonymous inner class",
        "description": """Summary
When using isExactlyInstanceOf and the actual value is an anonymous inner class, the message is confusing as it claims that the actual value is an "instance of null".
Example
    assertThat(x.red).isNotNull().isExactlyInstanceOf(A.class);
Will not fail isNotNull but fails on isExactlyInstanceOf with:
java.lang.AssertionError:
Expecting:
to be exactly an instance of:
but was an instance of:
This led me to believe the value in x.red is null, but it clearly isn't.
If it is not possible to detect the anonymous inner class type here  (it in this case is an anonymous implementation of the interface Provider) perhaps change the message to but was an instance of an anonymous class.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "assertj-core",
        "issue_number": "2547",
        "pr_number": "2549",
        "title": "Regression in `AbstractMapAssert#containsOnlyKeys` with Spring's `MultiValueMapAdapter`",
        "description": """Summary
We saw this when updating from AssertJ 3.19.0 to 3.20.0. It appears that AbstractMapAssert#containsOnlyKeys is mutating the map that we're asserting on, which leads to test failures in our case. This is happening on an instance of org.springframework.util.MultiValueMapAdapter
Example
var underlyingMap = new HashMap>();
underlyingMap.put("Hello", List.of("World"));
var multiValueMap = CollectionUtils.toMultiValueMap(underlyingMap);
// This assertion passes
assertThat(multiValueMap).containsOnlyKeys("Hello");
// This assertion fails, as `multiValueMap` and `underlyingMap` are now empty
assertThat(multiValueMap).containsOnlyKeys("Hello");
The issue seems to have been introduced in #2167, and is caused by this use of Map#remove on a "clone" of the Map being asserted on. In our case that Map is a Spring MultiValueMapAdapter, which delegates operations to the underlying Map that it was constructed from. The remove call on the clone delegates to multiValueMap#remove which in turn delegates to underlyingMap#remove.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "assertj-core",
        "issue_number": "2666",
        "pr_number": "2685",
        "title": "assertContainsIgnoringCase fails to compare i and I in tr_TR locale",
        "description": """See org.assertj.core.internal.Strings#assertContainsIgnoringCase
https://github.com/assertj/assertj-core/blob/9051a958e6ab0a750bb243060aef57001ab97e6e/src/main/java/org/assertj/core/internal/Strings.java#L528-L531
I would suggest adding https://github.com/policeman-tools/forbidden-apis verification to just ban toLowerCase(), toUpperCase() and other unsafe methods: #2664""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "checkstyle",
        "issue_number": "10144",
        "pr_number": "10839",
        "title": "ClassFanOutComplexity fails to count all classes in multicatch and implements clause, remove unused CheckUtil#createFullType method",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_metrics.html#ClassFanOutComplexity
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
➜  src cat Test.java
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.EmptyStackException;
public class Test {
    public static void main(String[] args) {
        try {
            System.out.println(args[7]);
            File myFile = new File("myfile.txt"); // 1
            InputStream stream = myFile.toURL().openStream(); // 2
        } catch (IOException  | EmptyStackException e) { // 3,4
        }
    }
}
➜  src java -jar checkstyle-8.43-all.jar -c config.xml Test.java
Starting audit...
[ERROR] /home/nick/Desktop/Tester/src/Test.java:6:1: Class Fan-Out Complexity is 3 (max allowed is 1). [ClassFanOutComplexity]
Audit done.
Checkstyle ends with 1 errors.
➜  src
">
➜  src javac Test.java
Note: Test.java uses or overrides a deprecated API.
Note: Recompile with -Xlint:deprecation for details.
➜  src cat config.xml
➜  src cat Test.java
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.util.EmptyStackException;
public class Test {
    public static void main(String[] args) {
        try {
            System.out.println(args[7]);
            File myFile = new File("myfile.txt"); // 1
            InputStream stream = myFile.toURL().openStream(); // 2
        } catch (IOException  | EmptyStackException e) { // 3,4
        }
    }
}
➜  src java -jar checkstyle-8.43-all.jar -c config.xml Test.java
Starting audit...
[ERROR] /home/nick/Desktop/Tester/src/Test.java:6:1: Class Fan-Out Complexity is 3 (max allowed is 1). [ClassFanOutComplexity]
Audit done.
Checkstyle ends with 1 errors.
➜  src
I would expect the "Class Fan-Out Complexity" to be 4.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "10810",
        "pr_number": "10825",
        "title": "StackOverflow Error in IndentationCheck on deeply concatenated strings",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_misc.html#Indentation
Noticed at #9622 (comment):
➜  javac Test.java
➜  java -jar checkstyle-9.0-all.jar -c config.xml Test.java
Starting audit...
Exception in thread "main" java.lang.Error: Error was thrown while processing Test.java
        at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:310)
        at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
        at com.puppycrawl.tools.checkstyle.Main.runCheckstyle(Main.java:409)
        at com.puppycrawl.tools.checkstyle.Main.runCli(Main.java:332)
        at com.puppycrawl.tools.checkstyle.Main.execute(Main.java:191)
        at com.puppycrawl.tools.checkstyle.Main.main(Main.java:126)
Caused by: java.lang.StackOverflowError
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:264)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.findLineNo(DetailAstImpl.java:361)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:267)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.findLineNo(DetailAstImpl.java:361)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:264)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:442)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
 ...
">➜  cat Test.java
public class Test {
    public void test() {
        String s = " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
...
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " +
                " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " " + " ";
    }
}
➜  cat Test.java | wc -l
3028
➜  cat config.xml
➜  javac Test.java
➜  java -jar checkstyle-9.0-all.jar -c config.xml Test.java
Starting audit...
Exception in thread "main" java.lang.Error: Error was thrown while processing Test.java
        at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:310)
        at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
        at com.puppycrawl.tools.checkstyle.Main.runCheckstyle(Main.java:409)
        at com.puppycrawl.tools.checkstyle.Main.runCli(Main.java:332)
        at com.puppycrawl.tools.checkstyle.Main.execute(Main.java:191)
        at com.puppycrawl.tools.checkstyle.Main.main(Main.java:126)
Caused by: java.lang.StackOverflowError
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:264)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.findLineNo(DetailAstImpl.java:361)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:267)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.findLineNo(DetailAstImpl.java:361)
        at com.puppycrawl.tools.checkstyle.DetailAstImpl.getLineNo(DetailAstImpl.java:264)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:442)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
        at com.puppycrawl.tools.checkstyle.checks.indentation.AbstractExpressionHandler.getFirstAst(AbstractExpressionHandler.java:453)
 ...
IndentationCheck is failing on a large number of string concatenations, the culprit is recursive calls to AbstractExpressionHandler#getFirstAst:
checkstyle/src/main/java/com/puppycrawl/tools/checkstyle/checks/indentation/AbstractExpressionHandler.java
         Line 453
      in
      1ce8eea
 realStart = getFirstAst(realStart, node);
Perhaps some iterative approach will provide better performance and solve this issue.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "10817",
        "pr_number": "10958",
        "title": "NPE in IllegalTypeCheck when checking a record (Java 14)",
        "description": """Hello,
https://checkstyle.org/config_coding.html#IllegalType
I'm trying JDK 16 with language-level 16 I've run into an NPE. I've discovered this on Checkstyle 9.0, but the same problem is still unresolved on the master branch.
Since the build is configured to run on 1.8, I had to modify the source+target language to allow for the reproducer test-case, which I've prepared here: fprochazka@0e18223, it's probably not ideal, but IMHO it should pass a verifiable reproducer.
if you run the IllegalTypeCheckTest from my commit, you'll see the following errors:
InputIllegalTypeTestRecordsPass fail
com.puppycrawl.tools.checkstyle.api.CheckstyleException: Exception was thrown while processing /home/fprochazka/devel/libs/checkstyle/checkstyle/src/test/resources/com/puppycrawl/tools/checkstyle/checks/coding/illegaltype/InputIllegalTypeTestRecordsPass.java
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:302)
	at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.getActualViolationsForFile(AbstractModuleTestSupport.java:442)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.verifyViolations(AbstractModuleTestSupport.java:416)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.verifyWithInlineConfigParser(AbstractModuleTestSupport.java:269)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheckTest.testValidateRecordsPass(IllegalTypeCheckTest.java:66)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:78)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:567)
	at org.junit.platform.commons.util.ReflectionUtils.invokeMethod(ReflectionUtils.java:725)
	at org.junit.jupiter.engine.execution.MethodInvocation.proceed(MethodInvocation.java:60)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain$ValidatingInvocation.proceed(InvocationInterceptorChain.java:131)
	at org.junit.jupiter.engine.extension.TimeoutExtension.intercept(TimeoutExtension.java:149)
	at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestableMethod(TimeoutExtension.java:140)
	at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestMethod(TimeoutExtension.java:84)
	at org.junit.jupiter.engine.execution.ExecutableInvoker$ReflectiveInterceptorCall.lambda$ofVoidMethod$0(ExecutableInvoker.java:115)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.lambda$invoke$0(ExecutableInvoker.java:105)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain$InterceptedInvocation.proceed(InvocationInterceptorChain.java:106)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.proceed(InvocationInterceptorChain.java:64)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.chainAndInvoke(InvocationInterceptorChain.java:45)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.invoke(InvocationInterceptorChain.java:37)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:104)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:98)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.lambda$invokeTestMethod$7(TestMethodTestDescriptor.java:214)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.invokeTestMethod(TestMethodTestDescriptor.java:210)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:135)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:66)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:151)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base/java.util.ArrayList.forEach(ArrayList.java:1511)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base/java.util.ArrayList.forEach(ArrayList.java:1511)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.submit(SameThreadHierarchicalTestExecutorService.java:35)
	at org.junit.platform.engine.support.hierarchical.HierarchicalTestExecutor.execute(HierarchicalTestExecutor.java:57)
	at org.junit.platform.engine.support.hierarchical.HierarchicalTestEngine.execute(HierarchicalTestEngine.java:54)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:108)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:88)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.lambda$execute$0(EngineExecutionOrchestrator.java:54)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.withInterceptedStreams(EngineExecutionOrchestrator.java:67)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:52)
	at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:96)
	at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:75)
	at com.intellij.junit5.JUnit5IdeaTestRunner.startRunnerWithArgs(JUnit5IdeaTestRunner.java:71)
	at com.intellij.rt.junit.IdeaTestRunner$Repeater.startRunnerWithArgs(IdeaTestRunner.java:33)
	at com.intellij.rt.junit.JUnitStarter.prepareStreamsAndStart(JUnitStarter.java:235)
	at com.intellij.rt.junit.JUnitStarter.main(JUnitStarter.java:54)
Caused by: java.lang.NullPointerException: Cannot invoke "com.puppycrawl.tools.checkstyle.api.DetailAST.getFirstChild()" because "modifiers" is null
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isContainVerifiableType(IllegalTypeCheck.java:516)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isVerifiable(IllegalTypeCheck.java:502)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitVariableDef(IllegalTypeCheck.java:577)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitToken(IllegalTypeCheck.java:477)
	at com.puppycrawl.tools.checkstyle.TreeWalker.notifyVisit(TreeWalker.java:335)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processIter(TreeWalker.java:406)
	at com.puppycrawl.tools.checkstyle.TreeWalker.walk(TreeWalker.java:273)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processFiltered(TreeWalker.java:154)
	at com.puppycrawl.tools.checkstyle.api.AbstractFileSetCheck.process(AbstractFileSetCheck.java:87)
	at com.puppycrawl.tools.checkstyle.Checker.processFile(Checker.java:328)
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:289)
	... 70 more
InputIllegalTypeTestInnerRecordsPass fail
com.puppycrawl.tools.checkstyle.api.CheckstyleException: Exception was thrown while processing /home/fprochazka/devel/libs/checkstyle/checkstyle/src/test/resources/com/puppycrawl/tools/checkstyle/checks/coding/illegaltype/InputIllegalTypeTestInnerRecordsPass.java
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:302)
	at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.getActualViolationsForFile(AbstractModuleTestSupport.java:442)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.verifyViolations(AbstractModuleTestSupport.java:416)
	at com.puppycrawl.tools.checkstyle.AbstractModuleTestSupport.verifyWithInlineConfigParser(AbstractModuleTestSupport.java:269)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheckTest.testValidateInnerRecordsPass(IllegalTypeCheckTest.java:74)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
	at java.base/jdk.internal.reflect.NativeMethodAccessorImpl.invoke(NativeMethodAccessorImpl.java:78)
	at java.base/jdk.internal.reflect.DelegatingMethodAccessorImpl.invoke(DelegatingMethodAccessorImpl.java:43)
	at java.base/java.lang.reflect.Method.invoke(Method.java:567)
	at org.junit.platform.commons.util.ReflectionUtils.invokeMethod(ReflectionUtils.java:725)
	at org.junit.jupiter.engine.execution.MethodInvocation.proceed(MethodInvocation.java:60)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain$ValidatingInvocation.proceed(InvocationInterceptorChain.java:131)
	at org.junit.jupiter.engine.extension.TimeoutExtension.intercept(TimeoutExtension.java:149)
	at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestableMethod(TimeoutExtension.java:140)
	at org.junit.jupiter.engine.extension.TimeoutExtension.interceptTestMethod(TimeoutExtension.java:84)
	at org.junit.jupiter.engine.execution.ExecutableInvoker$ReflectiveInterceptorCall.lambda$ofVoidMethod$0(ExecutableInvoker.java:115)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.lambda$invoke$0(ExecutableInvoker.java:105)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain$InterceptedInvocation.proceed(InvocationInterceptorChain.java:106)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.proceed(InvocationInterceptorChain.java:64)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.chainAndInvoke(InvocationInterceptorChain.java:45)
	at org.junit.jupiter.engine.execution.InvocationInterceptorChain.invoke(InvocationInterceptorChain.java:37)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:104)
	at org.junit.jupiter.engine.execution.ExecutableInvoker.invoke(ExecutableInvoker.java:98)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.lambda$invokeTestMethod$7(TestMethodTestDescriptor.java:214)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.invokeTestMethod(TestMethodTestDescriptor.java:210)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:135)
	at org.junit.jupiter.engine.descriptor.TestMethodTestDescriptor.execute(TestMethodTestDescriptor.java:66)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:151)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base/java.util.ArrayList.forEach(ArrayList.java:1511)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at java.base/java.util.ArrayList.forEach(ArrayList.java:1511)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.invokeAll(SameThreadHierarchicalTestExecutorService.java:41)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$6(NodeTestTask.java:155)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$8(NodeTestTask.java:141)
	at org.junit.platform.engine.support.hierarchical.Node.around(Node.java:137)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.lambda$executeRecursively$9(NodeTestTask.java:139)
	at org.junit.platform.engine.support.hierarchical.ThrowableCollector.execute(ThrowableCollector.java:73)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.executeRecursively(NodeTestTask.java:138)
	at org.junit.platform.engine.support.hierarchical.NodeTestTask.execute(NodeTestTask.java:95)
	at org.junit.platform.engine.support.hierarchical.SameThreadHierarchicalTestExecutorService.submit(SameThreadHierarchicalTestExecutorService.java:35)
	at org.junit.platform.engine.support.hierarchical.HierarchicalTestExecutor.execute(HierarchicalTestExecutor.java:57)
	at org.junit.platform.engine.support.hierarchical.HierarchicalTestEngine.execute(HierarchicalTestEngine.java:54)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:108)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:88)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.lambda$execute$0(EngineExecutionOrchestrator.java:54)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.withInterceptedStreams(EngineExecutionOrchestrator.java:67)
	at org.junit.platform.launcher.core.EngineExecutionOrchestrator.execute(EngineExecutionOrchestrator.java:52)
	at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:96)
	at org.junit.platform.launcher.core.DefaultLauncher.execute(DefaultLauncher.java:75)
	at com.intellij.junit5.JUnit5IdeaTestRunner.startRunnerWithArgs(JUnit5IdeaTestRunner.java:71)
	at com.intellij.rt.junit.IdeaTestRunner$Repeater.startRunnerWithArgs(IdeaTestRunner.java:33)
	at com.intellij.rt.junit.JUnitStarter.prepareStreamsAndStart(JUnitStarter.java:235)
	at com.intellij.rt.junit.JUnitStarter.main(JUnitStarter.java:54)
Caused by: java.lang.NullPointerException: Cannot invoke "com.puppycrawl.tools.checkstyle.api.DetailAST.getFirstChild()" because "modifiers" is null
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isContainVerifiableType(IllegalTypeCheck.java:516)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isVerifiable(IllegalTypeCheck.java:502)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitVariableDef(IllegalTypeCheck.java:577)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitToken(IllegalTypeCheck.java:477)
	at com.puppycrawl.tools.checkstyle.TreeWalker.notifyVisit(TreeWalker.java:335)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processIter(TreeWalker.java:406)
	at com.puppycrawl.tools.checkstyle.TreeWalker.walk(TreeWalker.java:273)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processFiltered(TreeWalker.java:154)
	at com.puppycrawl.tools.checkstyle.api.AbstractFileSetCheck.process(AbstractFileSetCheck.java:87)
	at com.puppycrawl.tools.checkstyle.Checker.processFile(Checker.java:328)
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:289)
	... 70 more
The interesting part is IMHO this:
java.lang.NullPointerException: Cannot invoke "com.puppycrawl.tools.checkstyle.api.DetailAST.getFirstChild()" because "modifiers" is null
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isContainVerifiableType(IllegalTypeCheck.java:516)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.isVerifiable(IllegalTypeCheck.java:502)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitVariableDef(IllegalTypeCheck.java:577)
	at com.puppycrawl.tools.checkstyle.checks.coding.IllegalTypeCheck.visitToken(IllegalTypeCheck.java:477)
	at com.puppycrawl.tools.checkstyle.TreeWalker.notifyVisit(TreeWalker.java:335)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processIter(TreeWalker.java:406)
	at com.puppycrawl.tools.checkstyle.TreeWalker.walk(TreeWalker.java:273)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processFiltered(TreeWalker.java:154)
	at com.puppycrawl.tools.checkstyle.api.AbstractFileSetCheck.process(AbstractFileSetCheck.java:87)
	at com.puppycrawl.tools.checkstyle.Checker.processFile(Checker.java:328)
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:289)
My configuration of the check is baked into the comment in the tested source file.
If I change
memberModifiers = LITERAL_PUBLIC, LITERAL_PROTECTED, LITERAL_STATIC
to
memberModifiers = (default)
it starts to pass
...
Am I configuring it incorrectly? IMHO it should not throw an NPE even when configured incorrectly.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "10835",
        "pr_number": "10840",
        "title": "JavadocMethod accessModifiers incorrectly interpreted for interface class",
        "description": """I have read check documentation: https://checkstyle.org/config_javadoc.html#JavadocMethod
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat YOUR_FILE.java
#[[PLACE YOU OUTPUT HERE]]
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.0-all.jar -c config.xml YOUR_FILE.java
Starting audit...
Audit done.">/var/tmp $ javac YOUR_FILE.java
#[[MAKE SURE THERE IS SUCCESSFUL COMPILATION]]
public interface MyInterface {
  /** Javadoc ok here. */
  void test();
  class MyClass {
    /** Missing parameter here. */
    public MyClass(Integer amount) {
    }
  }
}
/var/tmp $ cat config.xml
/var/tmp $ cat YOUR_FILE.java
#[[PLACE YOU OUTPUT HERE]]
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.0-all.jar -c config.xml YOUR_FILE.java
Starting audit...
Audit done.
I expect checkstyle to report constructor to have missing javadoc param. Reason for that is that interface of this inner class is implicitly considered public according to java specs (Some IDEs even mark explicit public keyword as unnecessary).
If I add public keyword to class declaration, constructor is reported by checkstyle as expected.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "checkstyle",
        "issue_number": "10855",
        "pr_number": "10857",
        "title": "UnusedImports error if there are only array references to a given class",
        "description": """slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ cat src/main/java/checkstyle/reproducer/UnusedImportBug.java
package checkstyle.reproducer;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
public class UnusedImportBug {
    private static final Set FOO;
    static {
        FOO = new HashSet<>();
        FOO.add( HashMap[].class.getName() );
    }
}
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ RUN_LOCALE="-Duser.language=en -Duser.country=US"
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ java $RUN_LOCALE -jar checkstyle-9.0.1-all.jar -c gradle/checkstyle/checkstyle.xml src/main/java/checkstyle/reproducer/UnusedImportBug.java
Starting audit...
[ERROR] /home/slovdahl/checkstyle-unused-import-bug-reproducer/src/main/java/checkstyle/reproducer/UnusedImportBug.java:3:8: Unused import - java.util.HashMap. [UnusedImports]
Audit done.
Checkstyle ends with 1 errors.
">slovdahl@desk:~/checkstyle-unused-import-bug-reproducer/src/main/java (main)$ javac checkstyle/reproducer/UnusedImportBug.java
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer/src/main/java (main)$
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ cat gradle/checkstyle/checkstyle.xml
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ cat src/main/java/checkstyle/reproducer/UnusedImportBug.java
package checkstyle.reproducer;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Set;
public class UnusedImportBug {
    private static final Set FOO;
    static {
        FOO = new HashSet<>();
        FOO.add( HashMap[].class.getName() );
    }
}
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ RUN_LOCALE="-Duser.language=en -Duser.country=US"
slovdahl@desk:~/checkstyle-unused-import-bug-reproducer (main)$ java $RUN_LOCALE -jar checkstyle-9.0.1-all.jar -c gradle/checkstyle/checkstyle.xml src/main/java/checkstyle/reproducer/UnusedImportBug.java
Starting audit...
[ERROR] /home/slovdahl/checkstyle-unused-import-bug-reproducer/src/main/java/checkstyle/reproducer/UnusedImportBug.java:3:8: Unused import - java.util.HashMap. [UnusedImports]
Audit done.
Checkstyle ends with 1 errors.
Describe what you expect in detail.
The UnusedImport error should not be triggered if an import is actually used.
MCVE: https://github.com/hiboxsystems/checkstyle-unused-import-bug-reproducer""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "10945",
        "pr_number": "10967",
        "title": "OperatorWrap with token ASSIGN too strict for annotations",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_whitespace.html#OperatorWrap
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat OperatorWrapExample.java
@Annotation(example = {
        "foo",
        "bar"
})
public class OperatorWrapExample {
    public String[] array = {
            "foo",
            "bar"
    };
}
@interface Annotation {
    String[] example();
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.1-all.jar -c config.xml OperatorWrapExample.java
Starting audit...
[ERROR] I:\_tmp\_checkstyle\OperatorWrapExample.java:1:21: '=' should be on a new line. [OperatorWrap]
Audit done.
Checkstyle ends with 1 errors.">/var/tmp $ javac OperatorWrapExample.java
/var/tmp $ cat config.xml
/var/tmp $ cat OperatorWrapExample.java
@Annotation(example = {
        "foo",
        "bar"
})
public class OperatorWrapExample {
    public String[] array = {
            "foo",
            "bar"
    };
}
@interface Annotation {
    String[] example();
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.1-all.jar -c config.xml OperatorWrapExample.java
Starting audit...
[ERROR] I:\_tmp\_checkstyle\OperatorWrapExample.java:1:21: '=' should be on a new line. [OperatorWrap]
Audit done.
Checkstyle ends with 1 errors.
In the above example, the array field allows the first element to be on a new line. If the same is done for an annotation, Checkstyle complains. The only way to "fix" this is to put the first element on the same line as the = {. I expect the same behaviour in annotations as in other code.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "10962",
        "pr_number": "10963",
        "title": "NPE in EqualsAvoidNull check when accessing string from base class with 'this' qualifier",
        "description": """Checkstyle ends with a NPE when a derived class accesses an String variable from a base class when the variable is accessed via 'this' qualifier. The check runs fine when the 'this.' is omitted.
This error appeared first in the Checkstyle version 8.29 we currently use but can be reprodued with the latest 9.1 version.
It appears on the checkstyle command line (as in the sample below), withing the checkstyle maven plugin and in the checkstyle Eclipse plugin.
The below command sequence demonstrates the error:
type DerivedClass.java
package com.fsp.test;
public class DerivedClass extends AbstractBaseClass
{
   public DerivedClass()
   {
      if ( this.stringFromBaseClass.equals("JKHKJ") ) System.out.println("Hello");
   }
}
C:\Temp\test>type checkstyle-config.xml
C:\Temp\test>java -Duser.language=en -Duser.country=US -jar c:\temp\checkstyle-9.1-all.jar -c checkstyle-config.xml  AbstractBaseClass.java DerivedClass.java
Starting audit...
com.puppycrawl.tools.checkstyle.api.CheckstyleException: Exception was thrown while processing DerivedClass.java
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:302)
	at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
	at com.puppycrawl.tools.checkstyle.Main.runCheckstyle(Main.java:409)
	at com.puppycrawl.tools.checkstyle.Main.runCli(Main.java:332)
	at com.puppycrawl.tools.checkstyle.Main.execute(Main.java:191)
	at com.puppycrawl.tools.checkstyle.Main.main(Main.java:126)
Caused by: java.lang.NullPointerException
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.getFieldType(EqualsAvoidNullCheck.java:545)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.isStringFieldOrVariableFromThisInstance(EqualsAvoidNullCheck.java:481)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.isCalledOnStringFieldOrVariable(EqualsAvoidNullCheck.java:439)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.checkMethodCall(EqualsAvoidNullCheck.java:356)
	at java.lang.Iterable.forEach(Iterable.java:75)
	at java.util.Collections$UnmodifiableCollection.forEach(Collections.java:1080)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:339)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:336)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:336)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.finishTree(EqualsAvoidNullCheck.java:242)
	at com.puppycrawl.tools.checkstyle.TreeWalker.notifyEnd(TreeWalker.java:319)
	at com.puppycrawl.tools.checkstyle.TreeWalker.walk(TreeWalker.java:274)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processFiltered(TreeWalker.java:154)
	at com.puppycrawl.tools.checkstyle.api.AbstractFileSetCheck.process(AbstractFileSetCheck.java:87)
	at com.puppycrawl.tools.checkstyle.Checker.processFile(Checker.java:328)
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:289)
	... 5 more
Checkstyle ends with 1 errors.">C:\Temp\test>type AbstractBaseClass.java
package com.fsp.test;
public abstract class AbstractBaseClass
{
   protected String stringFromBaseClass = "ABC";
}
C:\Temp\test>type DerivedClass.java
package com.fsp.test;
public class DerivedClass extends AbstractBaseClass
{
   public DerivedClass()
   {
      if ( this.stringFromBaseClass.equals("JKHKJ") ) System.out.println("Hello");
   }
}
C:\Temp\test>type checkstyle-config.xml
C:\Temp\test>java -Duser.language=en -Duser.country=US -jar c:\temp\checkstyle-9.1-all.jar -c checkstyle-config.xml  AbstractBaseClass.java DerivedClass.java
Starting audit...
com.puppycrawl.tools.checkstyle.api.CheckstyleException: Exception was thrown while processing DerivedClass.java
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:302)
	at com.puppycrawl.tools.checkstyle.Checker.process(Checker.java:221)
	at com.puppycrawl.tools.checkstyle.Main.runCheckstyle(Main.java:409)
	at com.puppycrawl.tools.checkstyle.Main.runCli(Main.java:332)
	at com.puppycrawl.tools.checkstyle.Main.execute(Main.java:191)
	at com.puppycrawl.tools.checkstyle.Main.main(Main.java:126)
Caused by: java.lang.NullPointerException
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.getFieldType(EqualsAvoidNullCheck.java:545)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.isStringFieldOrVariableFromThisInstance(EqualsAvoidNullCheck.java:481)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.isCalledOnStringFieldOrVariable(EqualsAvoidNullCheck.java:439)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.checkMethodCall(EqualsAvoidNullCheck.java:356)
	at java.lang.Iterable.forEach(Iterable.java:75)
	at java.util.Collections$UnmodifiableCollection.forEach(Collections.java:1080)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:339)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:336)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.traverseFieldFrameTree(EqualsAvoidNullCheck.java:336)
	at com.puppycrawl.tools.checkstyle.checks.coding.EqualsAvoidNullCheck.finishTree(EqualsAvoidNullCheck.java:242)
	at com.puppycrawl.tools.checkstyle.TreeWalker.notifyEnd(TreeWalker.java:319)
	at com.puppycrawl.tools.checkstyle.TreeWalker.walk(TreeWalker.java:274)
	at com.puppycrawl.tools.checkstyle.TreeWalker.processFiltered(TreeWalker.java:154)
	at com.puppycrawl.tools.checkstyle.api.AbstractFileSetCheck.process(AbstractFileSetCheck.java:87)
	at com.puppycrawl.tools.checkstyle.Checker.processFile(Checker.java:328)
	at com.puppycrawl.tools.checkstyle.Checker.processFiles(Checker.java:289)
	... 5 more
Checkstyle ends with 1 errors.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "11015",
        "pr_number": "11020",
        "title": "SimplifyBooleanExpression: A False negative about ternary operator",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_coding.html#SimplifyBooleanExpression
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat Test.java
public class Test {
    public boolean fun() {
        return False;
    }
    public boolean foo() {
        boolean tag = fun() ? True : False;  // should report a warning here
        // boolean tag = func() == True; // can be detected
        return tag;
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.2-all.jar -c ./config.xml Test.java
#[[PLACE YOUR OUTPUT HERE]]
Starting audit...
Audit done.">/var/tmp $ javac Test.java
/var/tmp $ cat config.xml
/var/tmp $ cat Test.java
public class Test {
    public boolean fun() {
        return False;
    }
    public boolean foo() {
        boolean tag = fun() ? True : False;  // should report a warning here
        // boolean tag = func() == True; // can be detected
        return tag;
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.2-all.jar -c ./config.xml Test.java
#[[PLACE YOUR OUTPUT HERE]]
Starting audit...
Audit done.
Describe what you expect in detail.
I have just found a False negative about the rule SimplifyBooleanExpression. Please refer to the below simplfied case. Here, I think fun() ? True : False  at line 6 is similar to func() == True. They all can be simplified into func().""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "checkstyle",
        "issue_number": "11031",
        "pr_number": "11085",
        "title": "StringLiteralEquality FN about String literal expression",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_coding.html#StringLiteralEquality
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat Test.java
class Test {
    public void foo() {
        String status = "pending";
        if (status == "do" + "ne") {} // violation
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-X.XX-all.jar -c config.xml Test.java
Starting audit...
Audit done.">/var/tmp $ javac Test.java
/var/tmp $ cat config.xml
/var/tmp $ cat Test.java
class Test {
    public void foo() {
        String status = "pending";
        if (status == "do" + "ne") {} // violation
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-X.XX-all.jar -c config.xml Test.java
Starting audit...
Audit done.
Describe what you expect in detail.
Hi, I found a False negative about the rule StringLiteralEquality. At line 4, it is obvious that right value is string literal, but no violation report. I think this is resulted by string literal expression. Thanks for your consideration.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "checkstyle",
        "issue_number": "11213",
        "pr_number": "11383",
        "title": "False positive: SummaryJavadocCheck",
        "description": """From comment1 and comment2
I have read check documentation: https://checkstyle.sourceforge.io/config_javadoc.html#SummaryJavadoc
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat Test2.java
// unexpected violation below
/**
 * This is the actual summary.
 * {@summary This is wrong usage}
 */
public class Test2 {
}
// expected violation below
/**
 * This is summary
 */
class foo {
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.2.1-all.jar -c config.xml Test2.java
Starting audit...
[ERROR] /home/vyom/IdeaProjects/ConfigCheckstyle/src/TestP/Test2.java:2: Summary of Javadoc is missing an ending period. [SummaryJavadoc]
[ERROR] /home/vyom/IdeaProjects/ConfigCheckstyle/src/TestP/Test2.java:10: First sentence of Javadoc is missing an ending period. [SummaryJavadoc]
Audit done.
Checkstyle ends with 2 errors.">/var/tmp $ javac Test2.java
/var/tmp $ cat config.xml
/var/tmp $ cat Test2.java
// unexpected violation below
/**
 * This is the actual summary.
 * {@summary This is wrong usage}
 */
public class Test2 {
}
// expected violation below
/**
 * This is summary
 */
class foo {
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.2.1-all.jar -c config.xml Test2.java
Starting audit...
[ERROR] /home/vyom/IdeaProjects/ConfigCheckstyle/src/TestP/Test2.java:2: Summary of Javadoc is missing an ending period. [SummaryJavadoc]
[ERROR] /home/vyom/IdeaProjects/ConfigCheckstyle/src/TestP/Test2.java:10: First sentence of Javadoc is missing an ending period. [SummaryJavadoc]
Audit done.
Checkstyle ends with 2 errors.
Describe what you expect in detail.
Starting audit...
[ERROR] /home/vyom/IdeaProjects/ConfigCheckstyle/src/TestP/Test2.java:10: First sentence of Javadoc is missing an ending period. [SummaryJavadoc]
Audit done.
If the first line is present then @summary is ignored, though a warning is given by the Javadoc tool.
Test.java:4: warning: invalid use of @summary
     * {@summary This is wrong usage}
see all details at #11051 (comment)
Expected: only violation on second javadoc""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "11268",
        "pr_number": "11270",
        "title": "False Negative: RedundantModifierCheck",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_modifier.html#RedundantModifier
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ cat Test.java
package tmp;
public interface Test {
    public static interface foo { // violation for 'static', no violation for 'public'
    }
    public static enum someEnum { // violation for both
    }
    public static class someClass { // violation for both
    }
    public static record someRecord() { // violation for none, will be fixed in #11259
    }
    public static @interface someAnnInterface { // violation for none
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.3-all.jar -c config.xml Test.java
Starting audit...
[ERROR] /var/tmp/Test.java:4:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:12: Redundant 'static' modifier. [RedundantModifier]
Audit done.
Checkstyle ends with 5 errors.
">/var/tmp $ javac Test.java
/var/tmp $ cat config.xml
/var/tmp $ cat Test.java
package tmp;
public interface Test {
    public static interface foo { // violation for 'static', no violation for 'public'
    }
    public static enum someEnum { // violation for both
    }
    public static class someClass { // violation for both
    }
    public static record someRecord() { // violation for none, will be fixed in #11259
    }
    public static @interface someAnnInterface { // violation for none
    }
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-9.3-all.jar -c config.xml Test.java
Starting audit...
[ERROR] /var/tmp/Test.java:4:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:12: Redundant 'static' modifier. [RedundantModifier]
Audit done.
Checkstyle ends with 5 errors.
Describe what you expect in detail.
Starting audit...
[ERROR] /var/tmp/Test.java:4:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:4:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:7:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:10:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:13:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:13:12: Redundant 'static' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:16:5: Redundant 'public' modifier. [RedundantModifier]
[ERROR] /var/tmp/Test.java:16:12: Redundant 'static' modifier. [RedundantModifier]
Audit done.
Checkstyle ends with 10 errors.
Every member class or interface declaration in the body of an interface declaration is implicitly public and static. See JLS for more info. Comments in code specify the current behavior.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "11365",
        "pr_number": "11468",
        "title": "FinalClassCheck: False positive with anonymous classes",
        "description": """I have read check documentation: https://checkstyle.sourceforge.io/config_design.html#FinalClass
I have downloaded the latest checkstyle from: https://checkstyle.org/cmdline.html#Download_and_Run
I have executed the cli and showed it below, as cli describes the problem better than 1,000 words
/var/tmp $ javac Test.java
/var/tmp $ cat config.xml
">xml version="1.0"?>
DOCTYPE module PUBLIC
        "-//Checkstyle//DTD Checkstyle Configuration 1.3//EN"
        "https://checkstyle.org/dtds/configuration_1_3.dtd">
    module>
module>
/var/tmp $ cat Test.java
public class Test {
    class a { // expected no violation
        private a() {
        }
    }
    a obj = new a() {
    };
}
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-10.0-all.jar -c config.xml Test.java
Starting audit...
[ERROR] /var/tmp/Test.java:3:5: Class a should be declared as final. [FinalClass]
Audit done.
Checkstyle ends with 1 errors.
Describe what you expect in detail.
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-10.0-all.jar -c config.xml Test.java
Starting audit...
Audit done.
This was supposed to be fixed in #9357. Making the class final results in a compile-time error.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "checkstyle",
        "issue_number": "11605",
        "pr_number": "11926",
        "title": "InvalidJavadocPosition: False positive for the generic constructor without access modifier",
        "description": """Check documentation: https://checkstyle.sourceforge.io/config_javadoc.html#InvalidJavadocPosition
/var/tmp $ javac Test.java
/var/tmp $ cat Test.java
public class Test {
    /**
    * Test
    */
     Test(E a) {
    }
}
/var/tmp $ cat config.xml
">
/var/tmp $ RUN_LOCALE="-Duser.language=en -Duser.country=US"
/var/tmp $ java $RUN_LOCALE -jar checkstyle-X.XX-all.jar -c config.xml Test.java
Starting audit...
[ERROR] C:\Projects\checkstyle\Test.java:2:5: Javadoc comment is placed in the wrong location. [InvalidJavadocPosition]
Audit done.
Checkstyle ends with 1 errors.
Expected: no validation error""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "gson",
        "issue_number": "847",
        "pr_number": "2060",
        "title": "LazilyParsedNumber being serialised as JsonObject",
        "description": """When I deserialise a JSON object into a map and back into JSON it seems to serialise the LazilyParsedNumber as an object.
JSON being parsed:
{
    "class": "Setting",
    "event": 4,
    "severity": 2,
    "notify": True,
    "sound": False,
    "feeds": [
        {
            "code": "USGS",
            "language": "eng"
        }
    ]
}
Class JSON is being parsed into
 settings = new HashMap<>();
    protected List feeds = new ArrayList<>();
}">@NoArgsConstructor
@AllArgsConstructor(suppressConstructorProperties = True)
@Accessors(chain = True) @Data
public class MonitoredLocationSetting
{
    @SerializedName("class") private final String className = "Setting";
    protected int event = -1;
    protected Map settings = new HashMap<>();
    protected List feeds = new ArrayList<>();
}
Basically all im doing is deserialising all fields except "event", "feeds", and "class" into the settings map using the following adapters
> entries = json.getAsJsonObject().entrySet().iterator();
            while (entries.hasNext())
            {
                Map.Entry next = entries.next();
                if (!fieldsToIgnore.contains(next.getKey()))
                {
                    if (next.getValue().isJsonPrimitive())
                    {
                        if (next.getValue().getAsJsonPrimitive().isBoolean())
                        {
                            setting.getSettings().put(next.getKey(), next.getValue().getAsBoolean());
                        }
                        else if (next.getValue().getAsJsonPrimitive().isNumber())
                        {
                            // This deserialises as LazilyParsedNumber
                            setting.getSettings().put(next.getKey(), next.getValue().getAsNumber());
                        }
                        else if (next.getValue().getAsJsonPrimitive().isString())
                        {
                            setting.getSettings().put(next.getKey(), next.getValue().getAsString());
                        }
                        else
                        {
                            setting.getSettings().put(next.getKey(), next.getValue());
                        }
                    }
                }
            }
        }
        return setting;
    }
});
builder.registerTypeAdapter(MonitoredLocationSetting.class, new JsonSerializer()
{
    @Override public JsonElement serialize(MonitoredLocationSetting src, Type typeOfSrc, JsonSerializationContext context)
    {
        JsonObject serialised = (JsonObject)new Gson().toJsonTree(src);
        // After the above line is called the following JSON is produced
        /*
                {
                    "class": "Setting",
                    "event": 4,
                    "feeds": [
                        {
                            "code": "USGS",
                            "language": "eng"
                        }
                    ],
                    "settings": {
                        "notify": True,
                        "severity": {   entries = setting.entrySet().iterator();
        while (entries.hasNext())
        {
            Map.Entry next = entries.next();
            serialised.add(next.getKey(), next.getValue());
        }
        serialised.remove("settings");
        return serialised;
    }
});">builder.registerTypeAdapter(MonitoredLocationSetting.class, new JsonDeserializer()
{
    @Override public MonitoredLocationSetting deserialize(JsonElement json, Type typeOfT, JsonDeserializationContext context) throws JsonParseException
    {
        MonitoredLocationSetting setting = new Gson().fromJson(json, typeOfT);
        if (setting != null)
        {
            // Ignore for setting.settings
            List fieldsToIgnore = new ArrayList(Arrays.asList(new String[]{"event", "feeds", "class"}));
            Iterator> entries = json.getAsJsonObject().entrySet().iterator();
            while (entries.hasNext())
            {
                Map.Entry next = entries.next();
                if (!fieldsToIgnore.contains(next.getKey()))
                {
                    if (next.getValue().isJsonPrimitive())
                    {
                        if (next.getValue().getAsJsonPrimitive().isBoolean())
                        {
                            setting.getSettings().put(next.getKey(), next.getValue().getAsBoolean());
                        }
                        else if (next.getValue().getAsJsonPrimitive().isNumber())
                        {
                            // This deserialises as LazilyParsedNumber
                            setting.getSettings().put(next.getKey(), next.getValue().getAsNumber());
                        }
                        else if (next.getValue().getAsJsonPrimitive().isString())
                        {
                            setting.getSettings().put(next.getKey(), next.getValue().getAsString());
                        }
                        else
                        {
                            setting.getSettings().put(next.getKey(), next.getValue());
                        }
                    }
                }
            }
        }
        return setting;
    }
});
builder.registerTypeAdapter(MonitoredLocationSetting.class, new JsonSerializer()
{
    @Override public JsonElement serialize(MonitoredLocationSetting src, Type typeOfSrc, JsonSerializationContext context)
    {
        JsonObject serialised = (JsonObject)new Gson().toJsonTree(src);
        // After the above line is called the following JSON is produced
        /*
                {
                    "class": "Setting",
                    "event": 4,
                    "feeds": [
                        {
                            "code": "USGS",
                            "language": "eng"
                        }
                    ],
                    "settings": {
                        "notify": True,
                        "severity": {  > entries = setting.entrySet().iterator();
        while (entries.hasNext())
        {
            Map.Entry next = entries.next();
            serialised.add(next.getKey(), next.getValue());
        }
        serialised.remove("settings");
        return serialised;
    }
});
From what I can see, technically this is correct because as far as Gson is concerned LazilyParsedNumber IS an object and not a 'primitive', however, doing a straight convert from and then back to json causes a problem because the object isnt parsed back as a primitive after being read as a primitive (Number)""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "gson",
        "issue_number": "1049",
        "pr_number": "2061",
        "title": "JsonReader.hasNext() returns True at END_DOCUMENT",
        "description": """JsonReader.hasNext() will return True if we are at the end of the document
(reader.peek() == JsonToken.END_DOCUMENT)""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "gson",
        "issue_number": "1127",
        "pr_number": "2130",
        "title": "JsonWriter don't work correctly with float",
        "description": """float x = 3.723379;
JsonWriter writer = ...
writer.value(x); //is will call value(double value), so it will wrong
result is 3.723378896713257
Please add new function for float.
Thank you.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "gson",
        "issue_number": "1831",
        "pr_number": "2153",
        "title": "Gson.getAdapter((TypeToken) null) throws exception",
        "description": """The Gson class has logic for handling null arguments for getAdapter(TypeToken), see:
gson/gson/src/main/java/com/google/gson/Gson.java
         Line 434
      in
      ceae88b
 TypeAdapter cached = typeTokenCache.get(type == null ? NULL_KEY_SURROGATE : type);
However, it appears the pull request which tried to keep the support for null arguments also broke it due to commit 31dcfa3 because it does not reassign a non-null value to the type argument anymore which later on in the method causes a NullPointerException.
However that was 4 years ago and it appears support for null arguments might not have been used much (if at all; I did not find existing issues about this here on GitHub). Therefore maybe it would be better instead of fixing this issue to simply remove null handling for getAdapter(TypeToken) completely and to throw an exception on purpose.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "gson",
        "issue_number": "2067",
        "pr_number": "2071",
        "title": "`EnumMap` deserialization fails with `ClassCastException`",
        "description": """Gson version
e2e851c
Java / Android version
openjdk version "11.0.13" 2021-10-19
OpenJDK Runtime Environment Temurin-11.0.13+8 (build 11.0.13+8)
OpenJDK 64-Bit Server VM Temurin-11.0.13+8 (build 11.0.13+8, mixed mode)
Description
EnumMap deserialization fails with ClassCastException:
java.lang.ClassCastException: class java.util.LinkedHashMap cannot be cast to class java.util.EnumMap
The underlying issue is related to #1708, it appears special handling for EnumMap is missing.
(I am a bit surprised that this issue has not been mentioned here anywhere before.)
Reproduction steps
Test case:
>() {}.getType();
  EnumMap actualMap = gson.fromJson("{\"VALUE1\":\"test\"}", type);
  Map expectedMap = Collections.singletonMap(MyEnum.VALUE1, "test");
  assertEquals(expectedMap, actualMap);
}">private static enum MyEnum {
  VALUE1, VALUE2
}
public void testEnumMap() throws Exception {
  EnumMap map = new EnumMap(MyEnum.class);
  map.put(MyEnum.VALUE1, "test");
  String json = gson.toJson(map);
  assertEquals("{\"VALUE1\":\"test\"}", json);
  Type type = new TypeToken>() {}.getType();
  EnumMap actualMap = gson.fromJson("{\"VALUE1\":\"test\"}", type);
  Map expectedMap = Collections.singletonMap(MyEnum.VALUE1, "test");
  assertEquals(expectedMap, actualMap);
}
Exception stack trace
Not really useful because ClassCastException occurs in user code.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "gson",
        "issue_number": "2133",
        "pr_number": "2134",
        "title": "ISO8061Utils.parse() accepts non-existent dates",
        "description": """Gson version
2.9.0
Java / Android version
java 16 2021-03-16
Java(TM) SE Runtime Environment (build 16+36-2231)
Java HotSpot(TM) 64-Bit Server VM (build 16+36-2231, mixed mode, sharing)
Description
Apparently ISO8061Utils.parse() works in a very lenient manner when dealing with dates that do not exist (for instance 2022-14-30), generating valid Date objects.
Given this unit test:
 @Test
    public void testDateParseNonExistentDate() throws ParseException {
        String dateStr = "2022-14-30";
        try {
            Date date = ISO8601Utils.parse(dateStr, new ParsePosition(0));
            fail("Should've thrown exception");
        } catch (Exception expected) {
        }
    }
It fails and produces a Date object whose toString() yields:
Thu Mar 02 00:00:00 BRT 2023
This also applies for instances where the day is invalid as well.
 @Test
    public void testDateParseNonExistentDate() throws ParseException {
        String dateStr = "2022-12-33";
        try {
            Date date = ISO8601Utils.parse(dateStr, new ParsePosition(0));
            fail("Should've thrown exception");
        } catch (Exception expected) {
        }
    }
It fails and produces a Date object whose toString() yields:
Mon Jan 02 00:00:00 BRT 2023
Expected behavior
An exception to be thrown, likely IllegalArgumentException.
Actual behavior
A valid Date object was generated that "absorbed" the surplus from the illegal argument.
Note
If this is expected behavior, let me know and I'll close the issue.""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "gson",
        "issue_number": "2156",
        "pr_number": "2158",
        "title": "Primitive type adapters don't perform numeric conversion during serialization",
        "description": """Gson version
2.9.0
Java / Android version
Java 17
Description
The built-in adapters for primitive types don't perform numeric conversion for serialization. This is most obvious when using Gson's non-typesafe method Gson.toJson(Object, Type):
System.out.println(new Gson().toJson(1.5, byte.class));
Even though the adapter for byte should be used, Gson nonetheless emits 1.5 as output.
I noticed that while trying to refactor the primitive type adapters to directly call the primitive JsonWriter.value methods instead of JsonWriter.value(Number) due to the overhead for checking if the string representation is a valid JSON number.
Expected behavior
Either narrowing / widening conversion should be performed or an exception should be thrown.
(Or are there legit use cases for this?)
Actual behavior
Gson just emits the Number.toString() result, even if that does not match the type of the requested adapter.
Reproduction steps
System.out.println(new Gson().toJson(1.5, byte.class));""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "hakky54",
        "issue_number": "166",
        "pr_number": "167",
        "title": "the alias of CertificateEntry",
        "description": """Describe the bug
Hello, I am going to create an SSLContext with the following code, but the resulting SSLContext does not appear to be complete and its trustedCerts is empty.
    SSLFactory sslFactory = SSLFactory.builder()
            .withTrustMaterial(CertificateUtils.loadCertificate("ca.crt"))
            .build();
    SSLContext sslContext = sslFactory.getSslContext();
the content of ca.crt
-----BEGIN CERTIFICATE-----
MIIFWTCCA0GgAwIBAgIUW4b6bPPPyRAm0DrDKKJJ8YlSqOkwDQYJKoZIhvcNAQEL
BQAwPDE6MDgGA1UEAxMxRWxhc3RpY3NlYXJjaCBzZWN1cml0eSBhdXRvLWNvbmZp
Z3VyYXRpb24gSFRUUCBDQTAeFw0yMjA0MDUxMjQ1MzVaFw0yNTA0MDQxMjQ1MzVa
MDwxOjA4BgNVBAMTMUVsYXN0aWNzZWFyY2ggc2VjdXJpdHkgYXV0by1jb25maWd1
cmF0aW9uIEhUVFAgQ0EwggIiMA0GCSqGSIb3DQEBAQUAA4ICDwAwggIKAoICAQDB
q3aR//NaqXBUqI0AVHuVWJmFMLYwpi/DQLUYifwOlGx4iAb6ePuiA8b7tXAGPn0z
TWFQ82t0DZf/1nXoRmNJO8ardAVWcL7z+VDUY7Hab08GJzRRP/V5b7VL+J+WBQOG
auN0cal3jM14k3FeZApyoL+XqmJ36MSY3WtAPfF3ySH1ltcMguXqN79k3Bxw0mGq
AJt+z4q8Lq2e8vsMKKpSO1vZ0grvffj6MBni2stfZ4ifA6Kubh/yePShKsG/N8nY
K6iJYjwLuVUQ1Eaw6X3s78c+eESTlzZiM6I7qTR1JzW5Fuyz/ZPbDcI1zg+p9H4g
NRaX76Fv9XG/XehLeYxNoTBLytY2d9kdEmW9MIGCqaROabDdxygxcJ5l3aqkBTiA
tq42vguuiQvpLndfGIEA4qh5AFyo+iqP1226+1onHfeXtbtyqjpHIV6RZa8RqNLg
ynmf96NzzHQq1CfKp5CgQB/l3yaAtFxguNyhKftHia518iTjcUpn9f3gmSzDlZy2
KgzZMaw8GwdtT+qac3XCVI7vwjY21uEHbCEklh8ZycAt28Dc0h747MqG9A3xdMDV
lf8iBtGjuxQNJSsOBRY6Up8ajEWeYvEqpKDHVHYxc78qdjGCzltgGIvjzah389mH
UC458l4Ey4Lns4C7NVAteHva9L71CE/zDTwJ3nECqwIDAQABo1MwUTAdBgNVHQ4E
FgQUphpsq/WD1QUsRkr9EQaGinawo9owHwYDVR0jBBgwFoAUphpsq/WD1QUsRkr9
EQaGinawo9owDwYDVR0TAQH/BAUwAwEB/zANBgkqhkiG9w0BAQsFAAOCAgEAlg8X
PnpSKIkt+a9imOFcddUgoNSCgwAyBuGdnUKTjuDnV2630O7cRky4Ly8gI3hxuV3j
I0JHatPA4Xw8m/8rAkgoega4zCQ89L7w8g1b54NnvnMOQIKs4aQ7TsYQUgyGxj6j
hhs1uLEBgF/uCJR1INZbiw4tjGTJssRSGMUsn7Mto0+3UL3AHqbmQY4IavRDEd2s
zpyGN1acwh9jl50pcKjgM/UYhNgWvGQgOF7MP8+4BWXBn9O7ufdUt4n08yPFP5hn
sOKrScnTCPIVn3uExcYDLDEuRDsQXfDvD03Bm6aFPC+qwr+W7k8WZPc7UW3vLzTg
TPtvnFwTunD3Bzv14b+2BOQH+caOKVyjBn73HzXQ6Xp8KM6ef3+6RZTeomHhqAwr
TG2vVsLzDhZiNjOE1Le3UeT4eAz7psgg+piouaXkY5FnVmMlNqWGkXfmvtMC8JzG
uWGUtSV2plImhQMgfrF4wMhntiNQcHa0Fge0k4I4ajt/HD5Al4yMYCMzx7ocbZLg
bTSDn+PuRt1NBZYC/Icz6L3CaSAVCMIEw145G/ytyu9annHs+hXSx+1ji3MHkF/g
yE65FKuMXoHLhCdN9MoKFEDr6eLlY7l9HWbcfQGpePoX4L/g1nGMVQmssCChkH5r
h5BvtLZEjAtAP6q1Al0phYV6eYQvLE8Dzbw0RQ0=
-----END CERTIFICATE-----
Environmental Data:
Java Version 1.8.0_202
sslcontext-kickstart Version 7.3.0
OS: Windows
Additional context
I found out the cause of the problem, when create X509TrustManagerImpl, its trustedCerts is already empty.
sun.security.ssl.X509TrustManagerImpl
sun.security.validator.KeyStores.getTrustedCerts(KeyStore var0)
java.security.KeyStore.isCertificateEntry(String alias)
sun.security.pkcs12.PKCS12KeyStore.engineIsCertificateEntry(String var1)
the entries keys has the capital letters, but the parameter var1 is lowercase letters
Can you consider changing alias to lowercase in the nl.altindag.ssl.util.KeyStoreUtils.createTrustStore(List certificates)
or nl.altindag.ssl.util.CertificateUtils.generateAlias(Certificate certificate)""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "hakky54",
        "issue_number": "196",
        "pr_number": "197",
        "title": "Version 7.4.3 fails to accept all certificates",
        "description": """Describe the bug
It seems that changes in version 7.4.3 skips accept-all truststore configured using
builder.withUnsafeTrustMaterial() or builder.withTrustingAllCertificatesWithoutValidation()
This is because UnsafeX509ExtendedTrustManager has 0 accepted X509Certificate
therefore it is skipped during checking in CombinableX509TrustManager
To Reproduce
SSLFactory.Builder builder = SSLFactory.builder().withDefaultTrustMaterial();
builder.withUnsafeTrustMaterial();
SSLFactory factory = builder.build();
SSLContext sslContext = factory.getSslContext();
SSLContext.setDefault(sslContext);
Expected behavior
Validation of the TLS certificate should pass and connection should be established
Environmental Data:
Java Version 11.0
Gradle
OS MacOS
Additional context
The test passes with 7.3.0 and 7.4.2""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "jackson-databind",
        "issue_number": "513",
        "pr_number": "3418",
        "title": "Empty list incorrectly deserialized when `ACCEPT_SINGLE_VALUE_AS_ARRAY` is enabled",
        "description": """When ACCEPT_SINGLE_VALUE_AS_ARRAY is enabled, an empty List is incorrectly deserialized as a list containing a single empty string (List.of("")). Test case:
", new TypeReference>() {});
        Assert.assertTrue(list.isEmpty());
    }
}">import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.dataformat.xml.XmlMapper;
import org.junit.Assert;
import org.junit.Test;
import java.util.List;
public class EmptyElementTest {
    @Test
    public void test() throws JsonProcessingException {
        XmlMapper mapper = new XmlMapper();
        mapper.enable(DeserializationFeature.ACCEPT_SINGLE_VALUE_AS_ARRAY);
        List list = mapper.readValue("", new TypeReference>() {});
        Assert.assertTrue(list.isEmpty());
    }
}
This is technically correct behavior, because  can be deserialized as an empty string, which can then be wrapped in a list. However imo this should still be fixed.
Looking at the code, the issue is in databind StringCollectionDeserializer. For the test case, isExpectedStartArrayToken returns False, which triggers the handleNonArray logic. This logic checks for the ACCEPT_SINGLE_VALUE_AS_ARRAY first, before trying to coerce the empty string to a list, which would succeed here.
I see two approaches to fix this. Either change FromXmlParser.isExpectedStartArrayToken to return True for an empty string token, or change StringCollectionDeserializer to attempt a coercion from empty string before wrapping the value. imo the former should work fine.
I can work on a fix for this once my corp CLA is cleared, which will be soon(tm).""",
        "bug_type": "crash",
        "is_crash": True
    },
    {
        "project": "jackson-databind",
        "issue_number": "3187",
        "pr_number": "3195",
        "title": "`AnnotatedMember.equals()` does not work reliably",
        "description": """Hi,
I noticed some strange behavior of the current AnnotatedMember.equals() implementations. Following test case for AnnotatedConstructor.equals() currently fails:
public void testAnnotatedConstructorEquality() {
    ObjectMapper mapper = new ObjectMapper();
    DeserializationConfig context = mapper.getDeserializationConfig();
    JavaType beanType = mapper.constructType(SomeBean.class);
    AnnotatedClass instance1 = AnnotatedClassResolver.resolve(context, beanType, context);
    AnnotatedClass instance2 = AnnotatedClassResolver.resolve(context, beanType, context);
    // Successful
    assertEquals(instance1, instance2);
    assertEquals(instance1.getDefaultConstructor().getAnnotated(), instance2.getDefaultConstructor().getAnnotated());
    // Fails
    assertEquals(instance1.getDefaultConstructor(), instance2.getDefaultConstructor());
}
Based on the first two successful assertEquals(...) statements, I would have expected that the third assertEquals(...) should be also successful. However, it currently fails.
The reason for this behavior is that AnnotatedConstructor.equals() is currently using == for comparing the two constructors:
public boolean equals(Object o) {
    if (o == this) return True;
    return ClassUtil.hasClass(o, getClass())
            && (((AnnotatedConstructor) o)._constructor == _constructor);
}
However, the implementation of the reflection API in java.lang.Class is always copying / cloning the Field, Method and Constructor instances prior to returning them to the caller (e.g. see Class.copyConstructors()). Thus, each call of Class.getConstructors() will always return new instances.
If you agree that the above test case should be successful (i.e. also assertEquals(instance1.getDefaultConstructor(), instance2.getDefaultConstructor()) should be successful), I would prepare a corresponding pull request that slightly modifies the current implementation of the equals() method for all subclasses of AnnotatedMember that are affected by this problem (i.e. at least AnnotatedField, AnnotatedConstructor and AnnotatedMethod).""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "jsoup",
        "issue_number": "1647",
        "pr_number": "1648",
        "title": "Allow attributes valid in html when converting from JSoup to W3C Document",
        "description": """Consider the following html document:
unicode attr names
">>
head>
  unicode attr namesp>
body>html>
Using v1.14.2 and running the following code:
unicode attr names";
        org.jsoup.nodes.Document jsoupDoc;
        jsoupDoc = Jsoup.parse(html);
        Document w3Doc = W3CDom.convert(jsoupDoc);
        System.out.println(W3CDom.asString(w3Doc, W3CDom.OutputHtml()));
    }">    public static void main(String[] args) {
        String html = "unicode attr names";
        org.jsoup.nodes.Document jsoupDoc;
        jsoupDoc = Jsoup.parse(html);
        Document w3Doc = W3CDom.convert(jsoupDoc);
        System.out.println(W3CDom.asString(w3Doc, W3CDom.OutputHtml()));
    }
Results in:
unicode attr names
">>
head>
  unicode attr namesp>
body>
html>
This is caused by W3CDOM.java#L346 hard-codes the syntax to xml. It can be easily fixed by checking the doctype of the output document and use that as the syntax.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "jsoup",
        "issue_number": "1764",
        "pr_number": "1763",
        "title": "Copy constructor of Safelist shares state",
        "description": """The copy constructor of Safelist public Safelist(Safelist copy) does not deep copy the data structures as advertised in the JavaDoc but shares the nested data structures, e.g. Map>. This causes unexpected mutation.
An example would be:
";
System.out.println(Jsoup.clean(html, safelist1));
System.out.println(Jsoup.clean(html, safelist2));">Safelist safelist1 = Safelist.none().addAttributes("foo", "bar");
Safelist safelist2 = new Safelist(safelist1);
safelist1.addAttributes("foo", "baz");
final String html = "";
System.out.println(Jsoup.clean(html, safelist1));
System.out.println(Jsoup.clean(html, safelist2));
The second output should not contain the baz attribute but does.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "hakky54",
        "issue_number": "121",
        "pr_number": "",
        "title": "Remove/Disable logging in unsafe HostnameVerifier and TrustManager",
        "description": """the logging in the unsafe variants of HostnameVerifier and TrustManager spam logs. There should be a way to disable this or at least log it to DEBUG.
I see no reason why i would like to know that a self signed certificate is trusted. that's exactly what i want to do else i wouldn't use this specific verifier.""",
        "bug_type": "semantic",
        "is_crash": False
    },
    {
        "project": "hakky54",
        "issue_number": "194",
        "pr_number": "",
        "title": "Support for Android keystore",
        "description": """""",
        "bug_type": "semantic",
        "is_crash": False
    },
]

def extract_bug_reports():
    """Extract GHRB bug reports with full metadata."""
    
    print("=" * 80)
    print("📋 Extracting GHRB Bug Reports")
    print("=" * 80)
    
    bug_reports = []
    repos_dir = Path("data/GHRB/repos")
    
    # Check if repos exist
    if not repos_dir.exists():
        print("\n⚠️  Warning: GHRB repos directory not found!")
        print("   Run: python3 scripts/setup_ghrb_complete.py first")
        return
    
    print(f"\nProcessing {len(GHRB_BUGS)} GHRB bugs...")
    
    for i, bug in enumerate(GHRB_BUGS, 1):
        project = bug['project']
        issue = bug['issue_number']
        
        print(f"\n[{i}/{len(GHRB_BUGS)}] {project} #{issue}")
        print(f"   Title: {bug['title'][:60]}...")
        
        # Check if repository exists
        repo_path = f"{repos_dir}\\repos\\{project}"
        
        print(f"   Repo Path: {repo_path}")
        repo_exists = Path(repo_path).exists()

        print(f"   Repository: {'Found' if repo_exists else 'Missing'}")
        
        bug_report = {
            "project": project,
            "issue_number": issue,
            "pr_number": bug.get("pr_number", ""),
            "title": bug["title"],
            "description": bug["description"],
            "bug_type": bug["bug_type"],
            "is_crash": bug["is_crash"],
            "repo_path": str(repo_path) if repo_exists else None,
            "source": "GHRB",
            "github_url": f"https://github.com/{project}/issues/{issue}"
        }
        
        bug_reports.append(bug_report)
    
    # Save bug reports
    output_file = Path("data/GHRB/bug_reports.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(bug_reports, f, indent=2)
    
    print("\n" + "=" * 80)
    print(f"✅ Extracted {len(bug_reports)} GHRB bug reports")
    print(f"   Saved to: {output_file}")
    print("=" * 80)
    
    # Statistics
    print("\n📊 Statistics:")
    
    from collections import Counter
    
    # By project
    project_counts = Counter(b['project'] for b in bug_reports)
    print("\n  By Project:")
    for project, count in sorted(project_counts.items()):
        print(f"    {project:20s}: {count:2d} bugs")
    
    # By type
    type_counts = Counter(b['bug_type'] for b in bug_reports)
    print("\n  By Type:")
    for bug_type, count in sorted(type_counts.items()):
        print(f"    {bug_type:20s}: {count:2d} bugs")
    
    # Crash vs non-crash
    crash_count = sum(1 for b in bug_reports if b['is_crash'])
    print(f"\n  Crash bugs: {crash_count}")
    print(f"  Semantic bugs: {len(bug_reports) - crash_count}")
    
    # Repos available
    available_repos = sum(1 for b in bug_reports if b['repo_path'])
    print(f"\n  Repositories available: {available_repos}/{len(bug_reports)}")
    
    if available_repos < len(bug_reports):
        print("\n  ⚠️  Some repositories are missing!")
        print("     Make sure you've extracted ghrb-repos.tar.gz correctly")

if __name__ == "__main__":
    extract_bug_reports()
